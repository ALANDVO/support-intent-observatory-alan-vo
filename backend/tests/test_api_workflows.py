"""Integration tests crossing the HTTP boundary for core ML workflows and OIDC token auth."""

import time
import jwt


def test_core_http_workflow_create_train_triage_resolve(client):
    ds_name = f"integration_test_dataset_{int(time.time() * 1000)}"
    # 1. Create a custom dataset
    dataset_payload = {
        "name": ds_name,
        "description": "Integration test support dataset",
        "tickets": [
            {"text": "Cancel my subscription immediately please", "actual_intent": "cancellation"},
            {"text": "Terminate our account renewal plan", "actual_intent": "cancellation"},
            {"text": "I want to cancel the recurring membership", "actual_intent": "cancellation"},
            {"text": "Please delete account and cancel plan", "actual_intent": "cancellation"},
            {"text": "Close and discontinue our subscription", "actual_intent": "cancellation"},
            {"text": "Billed twice on this invoice statement", "actual_intent": "billing_inquiry"},
            {"text": "Where is the PDF receipt for this payment?", "actual_intent": "billing_inquiry"},
            {"text": "Incorrect credit card charge on statement", "actual_intent": "billing_inquiry"},
            {"text": "Payment failed for monthly invoice", "actual_intent": "billing_inquiry"},
            {"text": "Need billing invoice breakdown", "actual_intent": "billing_inquiry"},
        ],
    }
    res_ds = client.post("/api/datasets", json=dataset_payload, headers={"X-Demo-Role": "operator"})
    assert res_ds.status_code == 201
    dataset_id = res_ds.json()["id"]

    # 2. Train a model on this dataset
    train_payload = {
        "name": "integration_model_v1",
        "dataset_id": dataset_id,
        "hyperparameters": {
            "ngram_min": 1,
            "ngram_max": 1,
            "c_regularization": 1.0,
            "test_size": 0.20,
        },
    }
    res_train = client.post("/api/models/train", json=train_payload, headers={"X-Demo-Role": "operator"})
    assert res_train.status_code == 201
    model_data = res_train.json()
    model_id = model_data["id"]
    assert model_data["status"] == "ready"
    assert model_data["accuracy"] is not None

    # 3. Retrieve evaluation data
    res_eval = client.get(f"/api/models/{model_id}/evaluation", headers={"X-Demo-Role": "viewer"})
    assert res_eval.status_code == 200
    eval_json = res_eval.json()
    assert "confusion_matrix" in eval_json
    assert "overall_metrics" in eval_json

    # 4. Triage an uncertain ticket to force human review
    triage_payload = {
        "text": "Uncertain ambiguous statement",
        "confidence_threshold": 0.99,  # Force review queue routing
        "margin_threshold": 0.50,
        "auto_route": True,
        "include_advisory": True,
    }
    res_triage = client.post("/api/tickets/triage", json=triage_payload, headers={"X-Demo-Role": "operator"})
    assert res_triage.status_code == 201
    triage_data = res_triage.json()
    assert triage_data["is_uncertain"] is True
    assert triage_data["routing_status"] == "human_review"
    assert triage_data["ticket_id"] is not None

    # 5. Inspect Review Queue
    res_queue = client.get("/api/review-queue?queue_status=pending", headers={"X-Demo-Role": "viewer"})
    assert res_queue.status_code == 200
    queue_items = res_queue.json()
    assert len(queue_items) > 0
    target_item = next((i for i in queue_items if i["ticket_id"] == triage_data["ticket_id"]), queue_items[0])

    # 6. Resolve Review Item
    resolve_payload = {
        "resolved_intent": "billing_inquiry",
        "reviewer_notes": "Confirmed billing issue",
        "add_to_training_dataset": True,
    }
    res_resolve = client.post(
        f"/api/review-queue/{target_item['id']}/resolve",
        json=resolve_payload,
        headers={"X-Demo-Role": "operator"},
    )
    assert res_resolve.status_code == 200
    assert res_resolve.json()["status"] == "resolved"
    assert res_resolve.json()["resolved_intent"] == "billing_inquiry"


def test_threshold_optimization_endpoint(client):
    """Test the threshold optimization endpoint returns valid thresholds."""
    # Create dataset
    ds_name = f"threshold_test_dataset_{int(time.time() * 1000)}"
    dataset_payload = {
        "name": ds_name,
        "description": "Threshold optimization test dataset",
        "tickets": [
            {"text": "Cancel my subscription immediately please", "actual_intent": "cancellation"},
            {"text": "Terminate our account renewal plan", "actual_intent": "cancellation"},
            {"text": "I want to cancel the recurring membership", "actual_intent": "cancellation"},
            {"text": "Please delete account and cancel plan", "actual_intent": "cancellation"},
            {"text": "Close and discontinue our subscription", "actual_intent": "cancellation"},
            {"text": "Billed twice on this invoice statement", "actual_intent": "billing_inquiry"},
            {"text": "Where is the PDF receipt for this payment?", "actual_intent": "billing_inquiry"},
            {"text": "Incorrect credit card charge on statement", "actual_intent": "billing_inquiry"},
            {"text": "Payment failed for monthly invoice", "actual_intent": "billing_inquiry"},
            {"text": "Need billing invoice breakdown", "actual_intent": "billing_inquiry"},
        ],
    }
    res_ds = client.post("/api/datasets", json=dataset_payload, headers={"X-Demo-Role": "operator"})
    assert res_ds.status_code == 201
    dataset_id = res_ds.json()["id"]

    # Train model
    train_payload = {
        "name": "threshold_test_model",
        "dataset_id": dataset_id,
        "hyperparameters": {
            "ngram_min": 1,
            "ngram_max": 1,
            "c_regularization": 1.0,
            "test_size": 0.20,
        },
    }
    res_train = client.post("/api/models/train", json=train_payload, headers={"X-Demo-Role": "operator"})
    assert res_train.status_code == 201
    model_id = res_train.json()["id"]

    # Optimize thresholds
    opt_payload = {
        "min_confidence": 0.5,
        "max_confidence": 0.95,
        "min_margin": 0.05,
        "max_margin": 0.5,
        "step": 0.05,
    }
    res_opt = client.post(
        f"/api/models/{model_id}/optimize-thresholds",
        json=opt_payload,
        headers={"X-Demo-Role": "operator"},
    )
    assert res_opt.status_code == 200
    opt_data = res_opt.json()

    # Validate response structure
    assert "optimal_confidence_threshold" in opt_data
    assert "optimal_margin_threshold" in opt_data
    assert "expected_auto_routed_rate" in opt_data
    assert "expected_auto_routed_accuracy" in opt_data
    assert "expected_review_queue_rate" in opt_data
    assert "threshold_curve" in opt_data
    assert isinstance(opt_data["threshold_curve"], list)
    assert len(opt_data["threshold_curve"]) > 0

    # Validate thresholds are in expected ranges
    assert 0.5 <= opt_data["optimal_confidence_threshold"] <= 0.95
    assert 0.05 <= opt_data["optimal_margin_threshold"] <= 0.5
    assert 0.0 <= opt_data["expected_auto_routed_rate"] <= 1.0
    assert 0.0 <= opt_data["expected_auto_routed_accuracy"] <= 1.0
    assert 0.0 <= opt_data["expected_review_queue_rate"] <= 1.0

    # Validate curve points
    for point in opt_data["threshold_curve"]:
        assert "confidence_threshold" in point
        assert "margin_threshold" in point
        assert "auto_routed_rate" in point
        assert "auto_routed_accuracy" in point
        assert "review_queue_rate" in point
        assert "score" in point


def test_oidc_bearer_token_propagation_and_rejection(client):
    # 1. Generate a synthetic valid JWT token
    now = time.time()
    valid_payload = {
        "sub": "oidc_user_42",
        "preferred_username": "sarah_operator",
        "email": "sarah@example.com",
        "exp": now + 3600,
        "role": "operator",
    }
    valid_token = jwt.encode(valid_payload, "test-symmetric-secret-key-32chars!", algorithm="HS256")

    # Propagate valid token into protected endpoint
    res_valid = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {valid_token}"},
    )
    assert res_valid.status_code == 200
    user_info = res_valid.json()
    assert user_info["username"] == "sarah_operator"
    assert user_info["role"] == "operator"
    assert user_info["auth_source"] == "oidc"

    # 2. Rejection of expired token
    expired_payload = {
        "sub": "expired_user",
        "exp": now - 3600,  # 1 hour in the past
        "role": "operator",
    }
    expired_token = jwt.encode(expired_payload, "test-symmetric-secret-key-32chars!", algorithm="HS256")
    res_expired = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert res_expired.status_code == 401
    assert "expired" in res_expired.json()["detail"].lower()

    # 3. Rejection of malformed token
    res_malformed = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer not-a-valid-jwt-token"},
    )
    assert res_malformed.status_code == 401
