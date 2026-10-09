"""Model training, evaluation reporting, and active model management endpoints."""

import json
import time
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_role
from app.models.entities import DatasetRecord, ModelTrainingRecord, EvaluationRecord, TicketRecord
from app.models.schemas import ModelTrainRequest, ModelResponse, EvaluationResponse, UserIdentity
from app.services.ml_engine import ml_engine
from app.services.audit_service import audit_service

router = APIRouter(prefix="/api/models", tags=["models"])


def _to_model_response(m: ModelTrainingRecord) -> ModelResponse:
    hparams = json.loads(m.hyperparameters) if m.hyperparameters else {}
    return ModelResponse(
        id=m.id,
        name=m.name,
        dataset_id=m.dataset_id,
        status=m.status,
        hyperparameters=hparams,
        train_sample_count=m.train_sample_count,
        test_sample_count=m.test_sample_count,
        accuracy=m.accuracy,
        macro_f1=m.macro_f1,
        weighted_f1=m.weighted_f1,
        training_latency_ms=m.training_latency_ms,
        is_active=m.is_active,
        created_at=m.created_at,
    )


@router.post("/train", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
def train_model(
    req: ModelTrainRequest,
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(require_role("operator")),
) -> ModelResponse:
    dataset = (
        db.query(DatasetRecord).filter(DatasetRecord.id == req.dataset_id).first()
        if req.dataset_id
        else db.query(DatasetRecord).order_by(DatasetRecord.created_at.desc()).first()
    )
    if not dataset:
        raise HTTPException(status_code=404, detail="No dataset found for training.")

    tickets = (
        db.query(TicketRecord)
        .filter(TicketRecord.dataset_id == dataset.id, TicketRecord.actual_intent.isnot(None))
        .all()
    )
    if len(tickets) < 10:
        raise HTTPException(status_code=400, detail=f"Dataset has only {len(tickets)} labeled tickets (minimum 10).")

    texts = [t.text for t in tickets]
    labels = [t.actual_intent for t in tickets]

    model_record = ModelTrainingRecord(
        name=req.name,
        dataset_id=dataset.id,
        status="training",
        hyperparameters=json.dumps(req.hyperparameters.model_dump()),
        is_active=False,
    )
    db.add(model_record)
    db.flush()

    start_time = time.time()
    try:
        eval_result = ml_engine.train_and_evaluate(
            texts=texts,
            labels=labels,
            hyperparams=req.hyperparameters.model_dump(),
            model_id=model_record.id,
        )
    except Exception as exc:
        model_record.status = "failed"
        db.commit()
        raise HTTPException(status_code=400, detail=f"Training failure: {exc}")

    duration_ms = round((time.time() - start_time) * 1000, 2)
    overall = eval_result["overall_metrics"]

    db.query(ModelTrainingRecord).filter(ModelTrainingRecord.is_active == True).update({"is_active": False})

    model_record.status = "ready"
    model_record.train_sample_count = eval_result["train_sample_count"]
    model_record.test_sample_count = eval_result["test_sample_count"]
    model_record.accuracy = overall["accuracy"]
    model_record.macro_f1 = overall["macro_f1"]
    model_record.weighted_f1 = overall["weighted_f1"]
    model_record.training_latency_ms = duration_ms
    model_record.model_file_path = eval_result["model_file_path"]
    model_record.is_active = True

    eval_record = EvaluationRecord(
        model_id=model_record.id,
        overall_metrics=json.dumps(overall),
        per_class_metrics=json.dumps(eval_result["per_class_metrics"]),
        confusion_matrix=json.dumps(eval_result["confusion_matrix"]),
        discriminative_features=json.dumps(eval_result["discriminative_features"]),
        baseline_comparison=json.dumps(eval_result["baseline_comparison"]),
    )
    db.add(eval_record)
    db.commit()
    db.refresh(model_record)

    audit_service.log_event(
        db=db,
        actor_username=current_user.username,
        actor_role=current_user.role,
        action="train_model",
        resource_type="model",
        resource_id=model_record.id,
        details={"name": model_record.name, "accuracy": model_record.accuracy},
    )
    return _to_model_response(model_record)


@router.get("", response_model=List[ModelResponse])
def list_models(
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(require_role("viewer")),
) -> List[ModelResponse]:
    records = db.query(ModelTrainingRecord).order_by(ModelTrainingRecord.created_at.desc()).all()
    return [_to_model_response(m) for m in records]


@router.get("/{model_id}", response_model=ModelResponse)
def get_model(
    model_id: str,
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(require_role("viewer")),
) -> ModelResponse:
    m = db.query(ModelTrainingRecord).filter(ModelTrainingRecord.id == model_id).first()
    if not m:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found.")
    return _to_model_response(m)


@router.post("/{model_id}/activate", response_model=ModelResponse)
def activate_model(
    model_id: str,
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(require_role("operator")),
) -> ModelResponse:
    m = db.query(ModelTrainingRecord).filter(ModelTrainingRecord.id == model_id).first()
    if not m:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found.")
    if m.status != "ready" or not m.model_file_path:
        raise HTTPException(status_code=400, detail="Model is not ready.")

    if not ml_engine.load_model(m.id, m.model_file_path):
        raise HTTPException(status_code=500, detail="Failed to load model artifact.")

    db.query(ModelTrainingRecord).filter(ModelTrainingRecord.is_active == True).update({"is_active": False})
    m.is_active = True
    db.commit()
    db.refresh(m)

    audit_service.log_event(
        db=db,
        actor_username=current_user.username,
        actor_role=current_user.role,
        action="activate_model",
        resource_type="model",
        resource_id=m.id,
    )
    return _to_model_response(m)


@router.get("/{model_id}/evaluation", response_model=EvaluationResponse)
def get_model_evaluation(
    model_id: str,
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(require_role("viewer")),
) -> EvaluationResponse:
    eval_rec = db.query(EvaluationRecord).filter(EvaluationRecord.model_id == model_id).first()
    if not eval_rec:
        raise HTTPException(status_code=404, detail=f"Evaluation record for model '{model_id}' not found.")

    return EvaluationResponse(
        id=eval_rec.id,
        model_id=eval_rec.model_id,
        overall_metrics=json.loads(eval_rec.overall_metrics),
        per_class_metrics=json.loads(eval_rec.per_class_metrics),
        confusion_matrix=json.loads(eval_rec.confusion_matrix),
        discriminative_features=json.loads(eval_rec.discriminative_features),
        baseline_comparison=json.loads(eval_rec.baseline_comparison),
        created_at=eval_rec.created_at,
    )
