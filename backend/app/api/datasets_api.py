"""Dataset management and exploration API endpoints."""

import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_role
from app.models.entities import DatasetRecord, TicketRecord
from app.models.schemas import (
    DatasetCreate,
    DatasetResponse,
    DatasetDetailResponse,
    UserIdentity,
)
from app.services.dataset_service import dataset_service
from app.services.audit_service import audit_service

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


@router.get("", response_model=List[DatasetResponse])
def list_datasets(
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(require_role("viewer")),
) -> List[DatasetResponse]:
    """Retrieves all registered datasets."""
    datasets = db.query(DatasetRecord).order_by(DatasetRecord.created_at.desc()).all()
    results = []
    for d in datasets:
        classes = json.loads(d.intent_classes) if d.intent_classes else []
        results.append(
            DatasetResponse(
                id=d.id,
                name=d.name,
                description=d.description,
                sample_count=d.sample_count,
                intent_classes=classes,
                created_at=d.created_at,
                updated_at=d.updated_at,
            )
        )
    return results


@router.get("/{dataset_id}", response_model=DatasetDetailResponse)
def get_dataset_details(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(require_role("viewer")),
) -> DatasetDetailResponse:
    """Retrieves detailed information, class distribution, and preview tickets for a dataset."""
    dataset = db.query(DatasetRecord).filter(DatasetRecord.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found.",
        )

    classes = json.loads(dataset.intent_classes) if dataset.intent_classes else []
    distribution = dataset_service.get_dataset_distribution(db, dataset.id)

    tickets = (
        db.query(TicketRecord)
        .filter(TicketRecord.dataset_id == dataset.id)
        .limit(20)
        .all()
    )
    preview = [
        {"id": t.id, "text": t.text, "actual_intent": t.actual_intent, "ref": t.external_ref}
        for t in tickets
    ]

    return DatasetDetailResponse(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        sample_count=dataset.sample_count,
        intent_classes=classes,
        class_distribution=distribution,
        preview_tickets=preview,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
    )


@router.post("", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
def create_dataset(
    req: DatasetCreate,
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(require_role("operator")),
) -> DatasetResponse:
    """Creates a new dataset from provided labeled tickets."""
    existing = db.query(DatasetRecord).filter(DatasetRecord.name == req.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dataset with name '{req.name}' already exists.",
        )

    unique_intents = sorted(list(set(t.actual_intent for t in req.tickets))) if req.tickets else []
    dataset = DatasetRecord(
        name=req.name,
        description=req.description,
        sample_count=len(req.tickets),
        intent_classes=json.dumps(unique_intents),
    )
    db.add(dataset)
    db.flush()

    for idx, t in enumerate(req.tickets):
        ticket = TicketRecord(
            dataset_id=dataset.id,
            external_ref=t.external_ref or f"TKT-{idx+1:04d}",
            text=t.text,
            actual_intent=t.actual_intent,
            routing_status="resolved",
        )
        db.add(ticket)

    db.commit()
    db.refresh(dataset)

    audit_service.log_event(
        db=db,
        actor_username=current_user.username,
        actor_role=current_user.role,
        action="create_dataset",
        resource_type="dataset",
        resource_id=dataset.id,
        details={"name": dataset.name, "sample_count": dataset.sample_count},
    )

    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        sample_count=dataset.sample_count,
        intent_classes=unique_intents,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
    )


@router.post("/seed", response_model=DatasetResponse)
def seed_default_corpus(
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(require_role("operator")),
) -> DatasetResponse:
    """Seeds the standard benchmark dataset if missing."""
    dataset = dataset_service.seed_default_dataset_if_empty(db)
    if not dataset:
        raise HTTPException(status_code=500, detail="Failed to seed default dataset.")

    audit_service.log_event(
        db=db,
        actor_username=current_user.username,
        actor_role=current_user.role,
        action="seed_dataset",
        resource_type="dataset",
        resource_id=dataset.id,
    )

    classes = json.loads(dataset.intent_classes) if dataset.intent_classes else []
    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        sample_count=dataset.sample_count,
        intent_classes=classes,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
    )
