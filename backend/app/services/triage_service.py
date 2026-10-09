"""Automated ticket triage, uncertainty routing, and queue management service."""

from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.entities import TicketRecord, ReviewQueueItem
from app.models.schemas import TriageRequest, TriageResponse, CandidateIntent, TokenHighlight
from app.services.ml_engine import ml_engine
from app.services.llm_service import llm_service


class TriageService:
    """Orchestrates model inference, uncertainty evaluation, and queue routing."""

    @staticmethod
    def triage_ticket(
        db: Session,
        req: TriageRequest,
        actor_username: str = "system",
    ) -> TriageResponse:
        conf_thresh = (
            req.confidence_threshold
            if req.confidence_threshold is not None
            else settings.default_confidence_threshold
        )
        margin_thresh = (
            req.margin_threshold
            if req.margin_threshold is not None
            else settings.default_margin_threshold
        )

        # 1. Run ML inference
        pred_result = ml_engine.predict(req.text)
        predicted_intent = pred_result["predicted_intent"]
        confidence = float(pred_result["confidence"])
        margin = float(pred_result["margin"])

        # 2. Evaluate uncertainty
        is_uncertain = False
        uncertainty_reason: Optional[str] = None

        if confidence < conf_thresh:
            is_uncertain = True
            uncertainty_reason = (
                f"Confidence {confidence:.2f} is below threshold {conf_thresh:.2f}"
            )
        elif margin < margin_thresh:
            is_uncertain = True
            uncertainty_reason = (
                f"Margin {margin:.2f} between top-2 candidates is below threshold {margin_thresh:.2f}"
            )

        routing_status = "human_review" if is_uncertain else "auto_routed"

        ticket_id: Optional[str] = None
        if req.auto_route:
            ticket = TicketRecord(
                external_ref=req.external_ref,
                text=req.text,
                predicted_intent=predicted_intent,
                confidence=confidence,
                margin=margin,
                is_uncertain=is_uncertain,
                routing_status=routing_status,
            )
            db.add(ticket)
            db.flush()
            ticket_id = ticket.id

            if is_uncertain:
                review_item = ReviewQueueItem(
                    ticket_id=ticket.id,
                    predicted_intent=predicted_intent,
                    confidence=confidence,
                    margin=margin,
                    uncertainty_reason=uncertainty_reason or "Low classification margin",
                    status="pending",
                )
                db.add(review_item)

            db.commit()

        # 3. Optional Advisory Insight
        advisory_payload = None
        if req.include_advisory:
            advisory = llm_service.generate_advisory(
                ticket_text=req.text,
                predicted_intent=predicted_intent,
                confidence=confidence,
                is_uncertain=is_uncertain,
            )
            advisory_payload = advisory.model_dump()

        candidates = [CandidateIntent(**c) for c in pred_result.get("candidates", [])]
        token_highlights = [TokenHighlight(**th) for th in pred_result.get("token_highlights", [])]

        return TriageResponse(
            ticket_id=ticket_id,
            text=req.text,
            predicted_intent=predicted_intent,
            confidence=confidence,
            margin=margin,
            is_uncertain=is_uncertain,
            uncertainty_reason=uncertainty_reason,
            routing_status=routing_status,
            candidates=candidates,
            token_highlights=token_highlights,
            advisory=advisory_payload,
        )


triage_service = TriageService()
