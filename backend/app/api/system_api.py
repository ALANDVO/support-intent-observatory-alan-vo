"""System status, health diagnostics, overview statistics, and audit logs."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import require_role
from app.models.entities import (
    DatasetRecord,
    TicketRecord,
    ModelTrainingRecord,
    ReviewQueueItem,
)
from app.models.schemas import (
    HealthResponse,
    SystemStatsResponse,
    AuditLogResponse,
    UserIdentity,
)
from app.services.ml_engine import ml_engine
from app.services.audit_service import audit_service

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/health", response_model=HealthResponse)
def healthcheck(db: Session = Depends(get_db)) -> HealthResponse:
    """Verifies service health, database connectivity, and active model state."""
    db_connected = True
    try:
        db.execute(DatasetRecord.__table__.select().limit(1))
    except Exception:
        db_connected = False

    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        demo_mode=settings.demo_mode,
        database_connected=db_connected,
        active_model_loaded=ml_engine.active_artifact is not None,
    )


@router.get("/stats", response_model=SystemStatsResponse)
def get_system_stats(
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(require_role("viewer")),
) -> SystemStatsResponse:
    """Computes high-level domain metrics for the dashboard summary."""
    dataset_cnt = db.query(DatasetRecord).count()
    ticket_cnt = db.query(TicketRecord).count()
    model_cnt = db.query(ModelTrainingRecord).count()
    pending_cnt = db.query(ReviewQueueItem).filter(ReviewQueueItem.status == "pending").count()
    resolved_cnt = db.query(ReviewQueueItem).filter(ReviewQueueItem.status == "resolved").count()

    active_model = (
        db.query(ModelTrainingRecord)
        .filter(ModelTrainingRecord.is_active == True)
        .first()
    )

    return SystemStatsResponse(
        dataset_count=dataset_cnt,
        ticket_count=ticket_cnt,
        model_count=model_cnt,
        pending_review_count=pending_cnt,
        resolved_review_count=resolved_cnt,
        active_model_name=active_model.name if active_model else None,
        active_model_accuracy=active_model.accuracy if active_model else None,
        active_model_macro_f1=active_model.macro_f1 if active_model else None,
    )


@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_trail(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    resource_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(require_role("admin")),
) -> List[AuditLogResponse]:
    """Retrieves transactional audit logs for security and compliance audits (Admin only)."""
    return audit_service.list_logs(
        db=db,
        limit=limit,
        offset=offset,
        resource_type=resource_type,
    )
