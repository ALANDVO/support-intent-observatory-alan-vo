"""Unit tests for triage service: inference, thresholding, and uncertainty routing."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.entities import TicketRecord, ReviewQueueItem
from app.models.schemas import TriageRequest
from app.services.ml_engine import ml_engine
from app.services.triage_service import triage_service


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    db = TestingSession()

    # Train a fast 2-class model on ml_engine
    texts = [
        "Please cancel my monthly subscription plan",
        "Terminate my subscription immediately",
        "I want to cancel the recurring membership",
        "Discontinue our team account before renewal",
        "Cancel our annual plan right away",
        "Why was my credit card billed twice?",
        "Need a receipt for the invoice payment",
        "Payment failed due to invalid card details",
        "Update billing address for corporate tax invoices",
        "There is an incorrect charge on our bill",
    ]
    labels = ["cancellation"] * 5 + ["billing_inquiry"] * 5
    ml_engine.train_and_evaluate(
        texts=texts,
        labels=labels,
        hyperparams={"ngram_min": 1, "ngram_max": 1, "test_size": 0.2},
        model_id="triage_test_mod",
    )

    yield db
    db.close()


def test_triage_confident_auto_route(test_db):
    req = TriageRequest(
        text="Please cancel our company recurring subscription plan immediately",
        confidence_threshold=0.60,
        margin_threshold=0.15,
        auto_route=True,
    )
    res = triage_service.triage_ticket(test_db, req, actor_username="analyst_1")

    assert res.predicted_intent == "cancellation"
    assert res.confidence >= 0.60
    assert not res.is_uncertain
    assert res.routing_status == "auto_routed"
    assert res.ticket_id is not None

    # Check persistence
    ticket = test_db.query(TicketRecord).filter(TicketRecord.id == res.ticket_id).first()
    assert ticket is not None
    assert ticket.routing_status == "auto_routed"

    # Ensure no review queue item was created for confident ticket
    review = test_db.query(ReviewQueueItem).filter(ReviewQueueItem.ticket_id == res.ticket_id).first()
    assert review is None


def test_triage_uncertain_low_confidence_routes_to_review(test_db):
    req = TriageRequest(
        text="Random ambiguous text about nothing in particular",
        confidence_threshold=0.99,  # Artificially high to guarantee uncertainty
        margin_threshold=0.01,
        auto_route=True,
    )
    res = triage_service.triage_ticket(test_db, req, actor_username="analyst_1")

    assert res.is_uncertain
    assert res.routing_status == "human_review"
    assert res.uncertainty_reason is not None
    assert "below threshold" in res.uncertainty_reason

    # Verify review queue record
    review = test_db.query(ReviewQueueItem).filter(ReviewQueueItem.ticket_id == res.ticket_id).first()
    assert review is not None
    assert review.status == "pending"
    assert review.confidence == res.confidence


def test_triage_uncertain_low_margin_routes_to_review(test_db):
    req = TriageRequest(
        text="Need help with account payment and cancel",
        confidence_threshold=0.10,
        margin_threshold=0.95,  # High margin required, should trigger uncertainty
        auto_route=True,
    )
    res = triage_service.triage_ticket(test_db, req, actor_username="analyst_1")

    assert res.is_uncertain
    assert res.routing_status == "human_review"
    assert "Margin" in res.uncertainty_reason
