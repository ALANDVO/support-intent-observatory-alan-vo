"""Ticket ingestion, automated triage, and classification endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_role
from app.models.entities import TicketRecord
from app.models.schemas import TriageRequest, TriageResponse, UserIdentity
from app.services.triage_service import triage_service
from app.services.audit_service import audit_service

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


@router.post("/triage", response_model=TriageResponse, status_code=status.HTTP_201_CREATED)
def triage_ticket_endpoint(
    req: TriageRequest,
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(require_role("operator")),
) -> TriageResponse:
    """
    Triages an incoming support ticket using the active ML intent model,
    calculates prediction confidence and margin, and routes uncertain tickets to human review.
    """
    response = triage_service.triage_ticket(
        db=db,
        req=req,
        actor_username=current_user.username,
    )

    audit_service.log_event(
        db=db,
        actor_username=current_user.username,
        actor_role=current_user.role,
        action="triage_ticket",
        resource_type="ticket",
        resource_id=response.ticket_id,
        details={
            "predicted_intent": response.predicted_intent,
            "confidence": response.confidence,
            "is_uncertain": response.is_uncertain,
            "routing_status": response.routing_status,
        },
    )

    return response


@router.get("")
def list_tickets(
    routing_status: Optional[str] = Query(None, description="Filter by routing status"),
    is_uncertain: Optional[bool] = Query(None, description="Filter by uncertainty flag"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(require_role("viewer")),
):
    """Lists persistent tickets with optional routing status and uncertainty filters."""
    query = db.query(TicketRecord)
    if routing_status:
        query = query.filter(TicketRecord.routing_status == routing_status)
    if is_uncertain is not None:
        query = query.filter(TicketRecord.is_uncertain == is_uncertain)

    total = query.count()
    tickets = query.order_by(TicketRecord.created_at.desc()).offset(offset).limit(limit).all()

    items = [
        {
            "id": t.id,
            "external_ref": t.external_ref,
            "text": t.text,
            "actual_intent": t.actual_intent,
            "predicted_intent": t.predicted_intent,
            "confidence": t.confidence,
            "margin": t.margin,
            "is_uncertain": t.is_uncertain,
            "routing_status": t.routing_status,
            "created_at": t.created_at,
        }
        for t in tickets
    ]

    return {"total": total, "limit": limit, "offset": offset, "items": items}


@router.get("/{ticket_id}")
def get_ticket(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(require_role("viewer")),
):
    """Retrieves full details for a single ticket."""
    ticket = db.query(TicketRecord).filter(TicketRecord.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket '{ticket_id}' not found.",
        )
    return {
        "id": ticket.id,
        "external_ref": ticket.external_ref,
        "text": ticket.text,
        "actual_intent": ticket.actual_intent,
        "predicted_intent": ticket.predicted_intent,
        "confidence": ticket.confidence,
        "margin": ticket.margin,
        "is_uncertain": ticket.is_uncertain,
        "routing_status": ticket.routing_status,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
    }
