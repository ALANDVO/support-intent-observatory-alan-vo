"""Audit logging service for transactional traceability of mutations and decisions."""

import json
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.entities import AuditLogRecord
from app.models.schemas import AuditLogResponse


class AuditService:
    """Manages transactional audit trail recording and querying."""

    @staticmethod
    def log_event(
        db: Session,
        actor_username: str,
        actor_role: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
    ) -> AuditLogRecord:
        """Appends an immutable audit log entry."""
        details_str = json.dumps(details) if details else None
        record = AuditLogRecord(
            actor_username=actor_username,
            actor_role=actor_role,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details_str,
            status=status,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def list_logs(
        db: Session,
        limit: int = 50,
        offset: int = 0,
        resource_type: Optional[str] = None,
    ) -> List[AuditLogResponse]:
        """Returns paginated audit log entries."""
        query = db.query(AuditLogRecord)
        if resource_type:
            query = query.filter(AuditLogRecord.resource_type == resource_type)

        records = query.order_by(AuditLogRecord.timestamp.desc()).offset(offset).limit(limit).all()
        results = []
        for r in records:
            details_dict = None
            if r.details:
                try:
                    details_dict = json.loads(r.details)
                except Exception:
                    details_dict = {"raw": r.details}

            results.append(
                AuditLogResponse(
                    id=r.id,
                    timestamp=r.timestamp,
                    actor_username=r.actor_username,
                    actor_role=r.actor_role,
                    action=r.action,
                    resource_type=r.resource_type,
                    resource_id=r.resource_id,
                    details=details_dict,
                    status=r.status,
                )
            )
        return results


audit_service = AuditService()
