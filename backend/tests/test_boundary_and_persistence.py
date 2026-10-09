"""Boundary condition tests, malformed input validation, and audit trail verification."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base
from app.models.entities import AuditLogRecord, DatasetRecord
from app.services.audit_service import audit_service

client = TestClient(app)


def test_empty_or_too_short_ticket_rejected():
    res = client.post(
        "/api/tickets/triage",
        json={"text": "a"},  # text min_length is 3
        headers={"X-Demo-Role": "operator"},
    )
    assert res.status_code == 422  # Validation error


def test_malformed_training_payload_rejected():
    res = client.post(
        "/api/models/train",
        json={"name": "x"},  # name min_length is 3
        headers={"X-Demo-Role": "operator"},
    )
    assert res.status_code == 422


def test_not_found_endpoints_return_404():
    res_model = client.get(
        "/api/models/non-existent-model-uuid",
        headers={"X-Demo-Role": "viewer"},
    )
    assert res_model.status_code == 404

    res_ticket = client.get(
        "/api/tickets/non-existent-ticket-uuid",
        headers={"X-Demo-Role": "viewer"},
    )
    assert res_ticket.status_code == 404

    res_resolve = client.post(
        "/api/review-queue/non-existent-item/resolve",
        json={"resolved_intent": "billing_inquiry"},
        headers={"X-Demo-Role": "operator"},
    )
    assert res_resolve.status_code == 404


def test_audit_service_transactional_logging():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    db = TestingSession()

    record = audit_service.log_event(
        db=db,
        actor_username="admin_user",
        actor_role="admin",
        action="update_hyperparameters",
        resource_type="model_config",
        resource_id="cfg_99",
        details={"c_reg": 2.5, "ngram_max": 2},
    )

    assert record.id is not None
    assert record.actor_username == "admin_user"
    assert record.action == "update_hyperparameters"

    # Query back
    logs = audit_service.list_logs(db=db, resource_type="model_config")
    assert len(logs) == 1
    assert logs[0].action == "update_hyperparameters"
    assert logs[0].details["c_reg"] == 2.5

    db.close()
