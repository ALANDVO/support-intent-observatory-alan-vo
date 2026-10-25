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

interface ThresholdOptimizationRequest {
  min_confidence?: number;
  max_confidence?: number;
  min_margin?: number;
  max_margin?: number;
  step?: number;
  target_auto_routed_rate?: number | null;
}

interface ThresholdOptimizationResponse {
  optimal_confidence_threshold: number;
  optimal_margin_threshold: number;
  expected_auto_routed_rate: number;
  expected_auto_routed_accuracy: number;
  expected_review_queue_rate: number;
  threshold_curve: Array<{
    confidence_threshold: number;
    margin_threshold: number;
    auto_routed_rate: number;
    auto_routed_accuracy: number;
    review_queue_rate: number;
    score: number;
  }>;
}

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
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    } else {
      headers["X-Demo-Role"] = this.demoRole;
    }

    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || ""}${path}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  async getProfile(): Promise<UserIdentity> {
    return this.request<UserIdentity>("/api/auth/me");
  }

  async demoLogin(role: string): Promise<UserIdentity> {
    return this.request<UserIdentity>("/api/auth/demo-login", {
      method: "POST",
      body: JSON.stringify({ role }),
    });
  }

  async getSystemStats(): Promise<SystemStats> {
    return this.request<SystemStats>("/api/system/stats");
  }

  async listDatasets(): Promise<Dataset[]> {
    return this.request<Dataset[]>("/api/datasets");
  }

  async getDatasetDetail(id: string): Promise<DatasetDetail> {
    return this.request<DatasetDetail>(`/api/datasets/${id}`);
  }

  async seedDataset(): Promise<Dataset> {
    return this.request<Dataset>("/api/datasets/seed", { method: "POST" });
  }

  async listModels(): Promise<ModelTrainingItem[]> {
    return this.request<ModelTrainingItem[]>("/api/models");
  }

  async trainModel(params: {
    name: string;
    dataset_id?: string;
    hyperparameters: Record<string, unknown>;
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

  async optimizeThresholds(modelId: string, params: ThresholdOptimizationRequest): Promise<ThresholdOptimizationResponse> {
    return this.request<ThresholdOptimizationResponse>(`/api/models/${modelId}/optimize-thresholds`, {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  async triageTicket(params: {
    text: string;
    external_ref?: string;
    include_advisory?: boolean;
  }): Promise<TriageResult> {
    return this.request<TriageResult>("/api/tickets/triage", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  async listReviewQueue(status: string = "pending"): Promise<ReviewQueueItem[]> {
    return this.request<ReviewQueueItem[]>(`/api/review-queue?queue_status=${status}`);
  }

  async getReviewStats(): Promise<ReviewStats> {
    return this.request<ReviewStats>("/api/review-queue/stats");
  }

  async resolveReviewItem(
    id: string,
    params: { resolved_intent: string; reviewer_notes?: string; add_to_training_dataset?: boolean }
  ): Promise<ReviewQueueItem> {
    return this.request<ReviewQueueItem>(`/api/review-queue/${id}/resolve`, {
      method: "POST",
      body: JSON.stringify(params),
    });
  }
}

export const api = new ApiClient();
</arg_key>
<arg_key=i>
Update API client with optimizeThresholds method
