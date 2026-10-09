"""Tests for authentication, role authorization, and security constraints."""

import pytest
from app.core.config import Settings


def test_unauthenticated_request_is_rejected(client):
    # Attempting to fetch tickets without auth or demo role header
    response = client.get("/api/tickets", headers={"Authorization": ""})
    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers


def test_viewer_role_access_and_denial(client):
    # Viewer can view datasets
    res_get = client.get("/api/datasets", headers={"X-Demo-Role": "viewer"})
    assert res_get.status_code == 200

    # Viewer cannot train models (operator or admin required)
    res_train = client.post(
        "/api/models/train",
        headers={"X-Demo-Role": "viewer"},
        json={"name": "unauthorized_model"},
    )
    assert res_train.status_code == 403
    assert "Insufficient permissions" in res_train.json()["detail"]


def test_operator_role_access_and_admin_denial(client):
    # Operator can view models
    res_get = client.get("/api/models", headers={"X-Demo-Role": "operator"})
    assert res_get.status_code == 200

    # Operator cannot inspect system audit logs (admin required)
    res_audit = client.get(
        "/api/system/audit-logs",
        headers={"X-Demo-Role": "operator"},
    )
    assert res_audit.status_code == 403
    assert "admin" in res_audit.json()["detail"].lower()


def test_admin_role_can_access_audit_logs(client):
    res = client.get(
        "/api/system/audit-logs",
        headers={"X-Demo-Role": "admin"},
    )
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_demo_mode_refused_in_production():
    prod_settings = Settings(
        ENVIRONMENT="production",
        DEMO_MODE=True,
    )
    with pytest.raises(RuntimeError, match="Demo mode cannot be enabled in production"):
        prod_settings.check_production_guard()
