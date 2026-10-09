"""Dataset management, seed corpus generation, and class distribution analytics."""

import json
from typing import Dict, Optional
from sqlalchemy.orm import Session
from app.models.entities import DatasetRecord, TicketRecord

SEED_SUPPORT_TICKETS = [
    # 1. Billing Inquiry
    {"text": "Why was my corporate credit card charged twice this billing cycle?", "intent": "billing_inquiry"},
    {"text": "Can you please send me a PDF receipt for the subscription renewal?", "intent": "billing_inquiry"},
    {"text": "I need to update our company billing address and tax ID on invoices.", "intent": "billing_inquiry"},
    {"text": "Our payment failed with error code card_declined. How do I retry?", "intent": "billing_inquiry"},
    {"text": "Where can our accounting team download annual billing statements in CSV?", "intent": "billing_inquiry"},

    # 2. Account Access
    {"text": "I forgot my password and the reset link emailed to me expires immediately.", "intent": "account_access"},
    {"text": "Two-factor SMS verification code is not being delivered to my phone.", "intent": "account_access"},
    {"text": "My user account was locked after three incorrect login attempts.", "intent": "account_access"},
    {"text": "How do I configure Okta SAML single sign-on for our engineering team?", "intent": "account_access"},
    {"text": "I lost access to my authenticator app and cannot provide the TOTP code.", "intent": "account_access"},

    # 3. Technical Issue
    {"text": "The REST API endpoint /v1/predictions is returning 500 internal server error.", "intent": "technical_issue"},
    {"text": "Our webhooks stopped receiving delivery events after 14:00 UTC today.", "intent": "technical_issue"},
    {"text": "The web dashboard UI crashes with an unhandled TypeError in browser console.", "intent": "technical_issue"},
    {"text": "Database sync latency is exceeding 15 seconds causing client timeouts.", "intent": "technical_issue"},
    {"text": "JSON payload parsing fails whenever our payload contains unicode characters.", "intent": "technical_issue"},

    # 4. Feature Request
    {"text": "Do you plan to support exporting metrics to Prometheus and OpenTelemetry?", "intent": "feature_request"},
    {"text": "Can you add an option for dark mode theme in the analytics reporting console?", "intent": "feature_request"},
    {"text": "We would like webhook HMAC signature verification to secure incoming events.", "intent": "feature_request"},
    {"text": "Please add support for custom regex validation rules on customer input fields.", "intent": "feature_request"},
    {"text": "Is it possible to add multi-region read replicas for lower latency?", "intent": "feature_request"},

    # 5. Cancellation
    {"text": "We would like to cancel our team subscription before renewal next month.", "intent": "cancellation"},
    {"text": "Please delete our organization account and purge all stored ticket data.", "intent": "cancellation"},
    {"text": "I want to discontinue our recurring enterprise plan effective immediately.", "intent": "cancellation"},
    {"text": "How do I turn off automatic renewal so our plan expires at end of term?", "intent": "cancellation"},
    {"text": "Our pilot evaluation project ended and we need to terminate this workspace.", "intent": "cancellation"},

    # 6. Refund Request
    {"text": "We were billed after requesting cancellation last week. Please process refund.", "intent": "refund_request"},
    {"text": "Can I get a refund for the unused months remaining on our annual agreement?", "intent": "refund_request"},
    {"text": "Our payment was accidentally processed twice on the same invoice, please refund.", "intent": "refund_request"},
    {"text": "We experienced platform downtime and request an SLA outage refund credit.", "intent": "refund_request"},
    {"text": "Please confirm when the refund of $590 will be credited back to our card.", "intent": "refund_request"},
]


class DatasetService:
    """Manages datasets, seed records, and ticket queries."""

    @staticmethod
    def seed_default_dataset_if_empty(db: Session) -> Optional[DatasetRecord]:
        existing = db.query(DatasetRecord).first()
        if existing:
            return existing

        intents = sorted(list(set(t["intent"] for t in SEED_SUPPORT_TICKETS)))
        dataset = DatasetRecord(
            name="customer_support_intent_benchmark",
            description="Benchmark dataset of realistic support inquiries across 6 operational intents.",
            sample_count=len(SEED_SUPPORT_TICKETS),
            intent_classes=json.dumps(intents),
        )
        db.add(dataset)
        db.flush()

        for idx, item in enumerate(SEED_SUPPORT_TICKETS):
            ticket = TicketRecord(
                dataset_id=dataset.id,
                external_ref=f"SEED-{idx+1:04d}",
                text=item["text"],
                actual_intent=item["intent"],
                routing_status="resolved",
            )
            db.add(ticket)

        db.commit()
        db.refresh(dataset)
        return dataset

    @staticmethod
    def get_dataset_distribution(db: Session, dataset_id: str) -> Dict[str, int]:
        tickets = db.query(TicketRecord).filter(TicketRecord.dataset_id == dataset_id).all()
        distribution: Dict[str, int] = {}
        for t in tickets:
            intent = t.actual_intent or "unlabeled"
            distribution[intent] = distribution.get(intent, 0) + 1
        return distribution


dataset_service = DatasetService()
