import {
  UserIdentity,
  Dataset,
  DatasetDetail,
  ModelTrainingItem,
  EvaluationData,
  TriageResult,
  ReviewQueueItem,
  ReviewStats,
  SystemStats,
} from "../types/api";

class ApiClient {
  private token: string | null = null;
  private demoRole: string = "operator";

  setToken(token: string | null) {
    this.token = token;
  }

  setDemoRole(role: string) {
    this.demoRole = role;
  }

  getDemoRole() {
    return this.demoRole;
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers = new Headers(options.headers || {});
    headers.set("Content-Type", "application/json");

    if (this.token) {
      headers.set("Authorization", `Bearer ${this.token}`);
    } else {
      headers.set("X-Demo-Role", this.demoRole);
    }

    const res = await fetch(path, {
      ...options,
      headers,
    });

    if (!res.ok) {
      let errorMsg = `HTTP Error ${res.status}`;
      try {
        const errorData = await res.json();
        errorMsg = errorData.detail || errorData.message || errorMsg;
      } catch {
        // Fallback to status text
      }
      throw new Error(errorMsg);
    }

    return res.json();
  }

  // Auth endpoints
  async getProfile(): Promise<UserIdentity> {
    return this.request<UserIdentity>("/api/auth/me");
  }

  async demoLogin(role: string): Promise<UserIdentity> {
    this.demoRole = role;
    return this.request<UserIdentity>("/api/auth/demo-login", {
      method: "POST",
      body: JSON.stringify({ role }),
    });
  }

  // System endpoints
  async getSystemStats(): Promise<SystemStats> {
    return this.request<SystemStats>("/api/system/stats");
  }

  // Datasets endpoints
  async listDatasets(): Promise<Dataset[]> {
    return this.request<Dataset[]>("/api/datasets");
  }

  async getDatasetDetail(id: string): Promise<DatasetDetail> {
    return this.request<DatasetDetail>(`/api/datasets/${id}`);
  }

  async seedDataset(): Promise<Dataset> {
    return this.request<Dataset>("/api/datasets/seed", { method: "POST" });
  }

  // Models endpoints
  async listModels(): Promise<ModelTrainingItem[]> {
    return this.request<ModelTrainingItem[]>("/api/models");
  }

  async trainModel(params: {
    name: string;
    dataset_id?: string | null;
    hyperparameters?: Record<string, unknown>;
  }): Promise<ModelTrainingItem> {
    return this.request<ModelTrainingItem>("/api/models/train", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  async activateModel(id: string): Promise<ModelTrainingItem> {
    return this.request<ModelTrainingItem>(`/api/models/${id}/activate`, {
      method: "POST",
    });
  }

  async getModelEvaluation(id: string): Promise<EvaluationData> {
    return this.request<EvaluationData>(`/api/models/${id}/evaluation`);
  }

  // Triage endpoints
  async triageTicket(params: {
    text: string;
    external_ref?: string;
    confidence_threshold?: number;
    margin_threshold?: number;
    include_advisory?: boolean;
  }): Promise<TriageResult> {
    return this.request<TriageResult>("/api/tickets/triage", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  // Review Queue endpoints
  async listReviewQueue(status: string = "pending"): Promise<ReviewQueueItem[]> {
    return this.request<ReviewQueueItem[]>(`/api/review-queue?queue_status=${status}`);
  }

  async getReviewStats(): Promise<ReviewStats> {
    return this.request<ReviewStats>("/api/review-queue/stats");
  }

  async resolveReviewItem(
    id: string,
    params: {
      resolved_intent: string;
      reviewer_notes?: string;
      add_to_training_dataset?: boolean;
    }
  ): Promise<ReviewQueueItem> {
    return this.request<ReviewQueueItem>(`/api/review-queue/${id}/resolve`, {
      method: "POST",
      body: JSON.stringify(params),
    });
  }
}

export const api = new ApiClient();
