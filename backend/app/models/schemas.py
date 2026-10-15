"""Pydantic schemas for API requests, responses, and serialization."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class UserIdentity(BaseModel):
    username: str
    email: Optional[str] = None
    role: str
    is_authenticated: bool = True
    auth_source: str = "oidc"


class DemoLoginRequest(BaseModel):
    role: str = Field(default="operator", description="Role to assume: viewer, operator, or admin")
    username: Optional[str] = "demo-analyst"


class TicketInput(BaseModel):
    text: str = Field(..., min_length=3, max_length=5000)
    actual_intent: str = Field(..., min_length=2, max_length=80)
    external_ref: Optional[str] = None


class DatasetCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=120)
    description: Optional[str] = None
    tickets: List[TicketInput] = Field(default_factory=list)


class DatasetResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    sample_count: int
    intent_classes: List[str]
    created_at: datetime
    updated_at: datetime


class DatasetDetailResponse(DatasetResponse):
    class_distribution: Dict[str, int]
    preview_tickets: List[Dict[str, Any]]


class HyperparametersSchema(BaseModel):
    ngram_min: int = Field(default=1, ge=1, le=3)
    ngram_max: int = Field(default=2, ge=1, le=3)
    min_df: int = Field(default=1, ge=1)
    max_df: float = Field(default=0.95, gt=0.0, le=1.0)
    c_regularization: float = Field(default=1.0, gt=0.01, le=100.0)
    max_iter: int = Field(default=500, ge=50, le=5000)
    test_size: float = Field(default=0.25, ge=0.1, le=0.5)


class ModelTrainRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=120)
    dataset_id: Optional[str] = None
    hyperparameters: HyperparametersSchema = Field(default_factory=HyperparametersSchema)


class ModelResponse(BaseModel):
    id: str
    name: str
    dataset_id: Optional[str] = None
    status: str
    hyperparameters: Dict[str, Any]
    train_sample_count: int
    test_sample_count: int
    accuracy: Optional[float] = None
    macro_f1: Optional[float] = None
    weighted_f1: Optional[float] = None
    training_latency_ms: Optional[float] = None
    is_active: bool
    created_at: datetime


class ConfusionMatrixSchema(BaseModel):
    labels: List[str]
    matrix: List[List[int]]
    normalized_matrix: List[List[float]]


class PerClassMetricSchema(BaseModel):
    precision: float
    recall: float
    f1_score: float
    support: int


class FeatureWeightItem(BaseModel):
    feature: str
    weight: float


class DiscriminativeFeaturesSchema(BaseModel):
    per_intent_features: Dict[str, List[FeatureWeightItem]]


class BaselineComparisonSchema(BaseModel):
    baseline_type: str
    baseline_accuracy: float
    model_accuracy: float
    accuracy_delta: float
    interpretation: str


class EvaluationResponse(BaseModel):
    id: str
    model_id: str
    overall_metrics: Dict[str, float]
    per_class_metrics: Dict[str, PerClassMetricSchema]
    confusion_matrix: ConfusionMatrixSchema
    discriminative_features: DiscriminativeFeaturesSchema
    baseline_comparison: BaselineComparisonSchema
    created_at: datetime


class TriageRequest(BaseModel):
    text: str = Field(..., min_length=3, max_length=5000)
    external_ref: Optional[str] = None
    confidence_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    margin_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    auto_route: bool = True
    include_advisory: bool = False


class CandidateIntent(BaseModel):
    intent: str
    probability: float


class TokenHighlight(BaseModel):
    token: str
    contribution: float


class TriageResponse(BaseModel):
    ticket_id: Optional[str] = None
    text: str
    predicted_intent: str
    confidence: float
    margin: float
    is_uncertain: bool
    uncertainty_reason: Optional[str] = None
    routing_status: str
    candidates: List[CandidateIntent]
    token_highlights: List[TokenHighlight]
    advisory: Optional[Dict[str, Any]] = None


class ReviewQueueItemResponse(BaseModel):
    id: str
    ticket_id: str
    ticket_text: str
    external_ref: Optional[str] = None
    predicted_intent: str
    confidence: float
    margin: float
    uncertainty_reason: str
    status: str  # pending, resolved, dismissed
    resolved_intent: Optional[str] = None
    reviewer_notes: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime


class ReviewResolveRequest(BaseModel):
    resolved_intent: str = Field(..., min_length=2, max_length=80)
    reviewer_notes: Optional[str] = None
    add_to_training_dataset: bool = True


class AdvisoryRequest(BaseModel):
    ticket_text: str = Field(..., min_length=3, max_length=5000)
    predicted_intent: str
    confidence: float
    is_uncertain: bool


class AdvisoryResponse(BaseModel):
    summary: str
    suggested_action: str
    key_signals: List[str]
    risk_assessment: str
    draft_response: str
    is_advisory: bool = True
    provider: str
    model: str


class AuditLogResponse(BaseModel):
    id: str
    timestamp: datetime
    actor_username: str
    actor_role: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    status: str


class SystemStatsResponse(BaseModel):
    dataset_count: int
    ticket_count: int
    model_count: int
    pending_review_count: int
    resolved_review_count: int
    active_model_name: Optional[str] = None
    active_model_accuracy: Optional[float] = None
    active_model_macro_f1: Optional[float] = None


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    environment: str
    demo_mode: bool
    database_connected: bool
    active_model_loaded: bool


class ThresholdOptimizationRequest(BaseModel):
    min_confidence: float = Field(default=0.5, ge=0.1, le=0.99)
    max_confidence: float = Field(default=0.95, ge=0.1, le=0.99)
    min_margin: float = Field(default=0.05, ge=0.0, le=0.5)
    max_margin: float = Field(default=0.5, ge=0.0, le=0.5)
    step: float = Field(default=0.025, ge=0.01, le=0.1)
    target_auto_routed_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class ThresholdCurvePoint(BaseModel):
    confidence_threshold: float
    margin_threshold: float
    auto_routed_rate: float
    auto_routed_accuracy: float
    review_queue_rate: float
    score: float


class ThresholdOptimizationResponse(BaseModel):
    optimal_confidence_threshold: float
    optimal_margin_threshold: float
    expected_auto_routed_rate: float
    expected_auto_routed_accuracy: float
    expected_review_queue_rate: float
    threshold_curve: List[ThresholdCurvePoint]
