export type UserRole = "viewer" | "operator" | "admin";

export interface UserIdentity {
  username: string;
  email?: string | null;
  role: UserRole;
  is_authenticated: boolean;
  auth_source: string;
}

export interface Dataset {
  id: string;
  name: string;
  description?: string | null;
  sample_count: number;
  intent_classes: string[];
  created_at: string;
  updated_at: string;
}

export interface DatasetDetail extends Dataset {
  class_distribution: Record<string, number>;
  preview_tickets: Array<{
    id: string;
    text: string;
    actual_intent: string;
    ref?: string | null;
  }>;
}

export interface ModelTrainingItem {
  id: string;
  name: string;
  dataset_id?: string | null;
  status: string;
  hyperparameters: Record<string, unknown>;
  train_sample_count: number;
  test_sample_count: number;
  accuracy?: number | null;
  macro_f1?: number | null;
  weighted_f1?: number | null;
  training_latency_ms?: number | null;
  is_active: boolean;
  created_at: string;
}

export interface PerClassMetric {
  precision: number;
  recall: number;
  f1_score: number;
  support: number;
}

export interface ConfusionMatrixData {
  labels: string[];
  matrix: number[][];
  normalized_matrix: number[][];
}

export interface FeatureWeight {
  feature: string;
  weight: number;
}

export interface EvaluationData {
  id: string;
  model_id: string;
  overall_metrics: {
    accuracy: number;
    macro_precision: number;
    macro_recall: number;
    macro_f1: number;
    weighted_precision: number;
    weighted_recall: number;
    weighted_f1: number;
  };
  per_class_metrics: Record<string, PerClassMetric>;
  confusion_matrix: ConfusionMatrixData;
  discriminative_features: {
    per_intent_features: Record<string, FeatureWeight[]>;
  };
  baseline_comparison: {
    baseline_type: string;
    baseline_accuracy: number;
    model_accuracy: number;
    accuracy_delta: number;
    interpretation: string;
  };
  created_at: string;
}

export interface CandidateIntent {
  intent: string;
  probability: number;
}

export interface TokenHighlight {
  token: string;
  contribution: number;
}

export interface AdvisoryData {
  summary: string;
  suggested_action: string;
  key_signals: string[];
  risk_assessment: "low" | "medium" | "high";
  draft_response: string;
  is_advisory: boolean;
  provider: string;
  model: string;
}

export interface TriageResult {
  ticket_id?: string | null;
  text: string;
  predicted_intent: string;
  confidence: number;
  margin: number;
  is_uncertain: boolean;
  uncertainty_reason?: string | null;
  routing_status: "auto_routed" | "human_review" | "resolved";
  candidates: CandidateIntent[];
  token_highlights: TokenHighlight[];
  advisory?: AdvisoryData | null;
}

export interface ReviewQueueItem {
  id: string;
  ticket_id: string;
  ticket_text: string;
  external_ref?: string | null;
  predicted_intent: string;
  confidence: number;
  margin: number;
  uncertainty_reason: string;
  status: "pending" | "resolved" | "dismissed";
  resolved_intent?: string | null;
  reviewer_notes?: string | null;
  resolved_by?: string | null;
  resolved_at?: string | null;
  created_at: string;
}

export interface ReviewStats {
  pending_count: number;
  resolved_count: number;
  dismissed_count: number;
  total_queued: number;
}

export interface SystemStats {
  dataset_count: number;
  ticket_count: number;
  model_count: number;
  pending_review_count: number;
  resolved_review_count: number;
  active_model_name?: string | null;
  active_model_accuracy?: number | null;
  active_model_macro_f1?: number | null;
}
