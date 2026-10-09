"""Human-in-the-loop review queue API endpoints."""

import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_role
from app.models.entities import ReviewQueueItem, TicketRecord, DatasetRecord
from app.models.schemas import (
    ReviewQueueItemResponse,
    ReviewResolveRequest,
    UserIdentity,
)
from app.services.audit_service import audit_service

router = APIRouter(prefix="/api/review-queue", tags=["review-queue"])


@router.get("", response_model=List[ReviewQueueItemResponse])
def list_review_items(
    queue_status: Optional[str] = Query("pending", description="Filter by status: pending, resolved, dismissed, or all"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(require_role("viewer")),
) -> List[ReviewQueueItemResponse]:
    """Retrieves items queued for human review with associated ticket context."""
    query = db.query(ReviewQueueItem).join(TicketRecord)
    if queue_status and queue_status != "all":
        query = query.filter(ReviewQueueItem.status == queue_status)

    items = query.order_by(ReviewQueueItem.created_at.desc()).offset(offset).limit(limit).all()
    results = []
    for item in items:
        results.append(
            ReviewQueueItemResponse(
                id=item.id,
                ticket_id=item.ticket_id,
                ticket_text=item.ticket.text,
                external_ref=item.ticket.external_ref,
                predicted_intent=item.predicted_intent,
                confidence=item.confidence,
                margin=item.margin,
                uncertainty_reason=item.uncertainty_reason,
                status=item.status,
                resolved_intent=item.resolved_intent,
                reviewer_notes=item.reviewer_notes,
                resolved_by=item.resolved_by,
                resolved_at=item.resolved_at,
                created_at=item.created_at,
            )
        )
    return results


@router.get("/stats")
def get_review_stats(
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(require_role("viewer")),
):
    """Returns aggregated review queue metrics."""
    pending = db.query(ReviewQueueItem).filter(ReviewQueueItem.status == "pending").count()
    resolved = db.query(ReviewQueueItem).filter(ReviewQueueItem.status == "resolved").count()
    dismissed = db.query(ReviewQueueItem).filter(ReviewQueueItem.status == "dismissed").count()
    return {
        "pending_count": pending,
        "resolved_count": resolved,
        "dismissed_count": dismissed,
        "total_queued": pending + resolved + dismissed,
    }


@router.post("/{item_id}/resolve", response_model=ReviewQueueItemResponse)
def resolve_review_item(
    item_id: str,
    req: ReviewResolveRequest,
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(require_role("operator")),
) -> ReviewQueueItemResponse:
    """
    Resolves an uncertain ticket review item by confirming or re-labeling intent,
    updating the ticket record, and optionally adding it back to training data.
    """
    item = db.query(ReviewQueueItem).filter(ReviewQueueItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review queue item '{item_id}' not found.",
        )

    now = datetime.datetime.now(datetime.timezone.utc)
    item.status = "resolved"
    item.resolved_intent = req.resolved_intent
    item.reviewer_notes = req.reviewer_notes
    item.resolved_by = current_user.username
    item.resolved_at = now

    ticket = db.query(TicketRecord).filter(TicketRecord.id == item.ticket_id).first()
    if ticket:
        ticket.actual_intent = req.resolved_intent
        ticket.routing_status = "resolved"
        ticket.is_uncertain = False

        # Add to active dataset if requested
        if req.add_to_training_dataset and not ticket.dataset_id:
            active_dataset = db.query(DatasetRecord).order_by(DatasetRecord.created_at.desc()).first()
            if active_dataset:
                ticket.dataset_id = active_dataset.id
                active_dataset.sample_count += 1

    db.commit()
    db.refresh(item)

    audit_service.log_event(
        db=db,
        actor_username=current_user.username,
        actor_role=current_user.role,
        action="resolve_review_item",
        resource_type="review_queue",
        resource_id=item.id,
        details={
            "ticket_id": item.ticket_id,
            "resolved_intent": item.resolved_intent,
            "resolved_by": item.resolved_by,
        },
    )

    return ReviewQueueItemResponse(
        id=item.id,
        ticket_id=item.ticket_id,
        ticket_text=ticket.text if ticket else "",
        external_ref=ticket.external_ref if ticket else None,
        predicted_intent=item.predicted_intent,
        confidence=item.confidence,
        margin=item.margin,
        uncertainty_reason=item.uncertainty_reason,
        status=item.status,
        resolved_intent=item.resolved_intent,
        reviewer_notes=item.reviewer_notes,
        resolved_by=item.resolved_by,
        resolved_at=item.resolved_at,
        created_at=item.created_at,
    )
