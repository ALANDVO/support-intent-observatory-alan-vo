"""Tests for LLM adapters with mocked network responses and offline fallbacks."""

from unittest.mock import patch, MagicMock
from app.services.llm_service import LLMService
from app.core.config import settings


def test_offline_fallback_when_no_api_key():
    service = LLMService()
    # Ensure offline fallback is used when no key is set
    with patch.object(settings, "llm_api_key", None), patch.object(settings, "llm_provider", "openai-compatible"):
        advisory = service.generate_advisory(
            ticket_text="How do I cancel my subscription before renewal?",
            predicted_intent="cancellation",
            confidence=0.88,
            is_uncertain=False,
        )

        assert advisory.is_advisory is True
        assert advisory.provider == "deterministic-offline-rule-engine"
        assert advisory.risk_assessment == "low"
        assert "cancellation" in advisory.summary.lower()
        assert len(advisory.key_signals) > 0


def test_openai_adapter_mocked_success():
    service = LLMService()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": (
                        '{"summary": "Billing query regarding invoice double charge", '
                        '"suggested_action": "Verify charge and issue refund credit.", '
                        '"key_signals": ["charge", "card"], "risk_assessment": "medium", '
                        '"draft_response": "We are investigating your invoice."}'
                    )
                }
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch.object(settings, "llm_api_key", "synthetic-test-key-000"), \
         patch.object(settings, "llm_provider", "openai-compatible"), \
         patch("httpx.Client.post", return_value=mock_response):
        advisory = service.generate_advisory(
            ticket_text="Double charge on card",
            predicted_intent="billing_inquiry",
            confidence=0.92,
            is_uncertain=False,
        )

        assert advisory.is_advisory is True
        assert advisory.provider == "openai-compatible"
        assert advisory.risk_assessment == "medium"
        assert "investigating" in advisory.draft_response


def test_anthropic_adapter_mocked_success():
    service = LLMService()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "content": [
            {
                "text": (
                    '{"summary": "Account password lockout", '
                    '"suggested_action": "Send security reset link.", '
                    '"key_signals": ["password", "lockout"], "risk_assessment": "high", '
                    '"draft_response": "Please reset your password."}'
                )
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch.object(settings, "llm_api_key", "synthetic-test-key-000"), \
         patch.object(settings, "llm_provider", "anthropic"), \
         patch("httpx.Client.post", return_value=mock_response):
        advisory = service.generate_advisory(
            ticket_text="Account locked after password attempts",
            predicted_intent="account_access",
            confidence=0.95,
            is_uncertain=False,
        )

        assert advisory.provider == "anthropic"
        assert advisory.risk_assessment == "high"


def test_gemini_adapter_mocked_success():
    service = LLMService()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": (
                                '{"summary": "Feature request for dark mode", '
                                '"suggested_action": "Catalog for product roadmap.", '
                                '"key_signals": ["dark mode"], "risk_assessment": "low", '
                                '"draft_response": "Thanks for your feedback."}'
                            )
                        }
                    ]
                }
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch.object(settings, "llm_api_key", "synthetic-test-key-000"), \
         patch.object(settings, "llm_provider", "gemini"), \
         patch("httpx.Client.post", return_value=mock_response):
        advisory = service.generate_advisory(
            ticket_text="Can you add dark mode?",
            predicted_intent="feature_request",
            confidence=0.89,
            is_uncertain=False,
        )

        assert advisory.provider == "gemini"
        assert advisory.risk_assessment == "low"


def test_provider_network_error_gracefully_falls_back():
    service = LLMService()
    with patch.object(settings, "llm_api_key", "synthetic-test-key-000"), \
         patch.object(settings, "llm_provider", "openai-compatible"), \
         patch("httpx.Client.post", side_effect=Exception("Connection timeout to upstream provider")):
        advisory = service.generate_advisory(
            ticket_text="Network timeout test",
            predicted_intent="technical_issue",
            confidence=0.75,
            is_uncertain=False,
        )

        # Must fall back gracefully to deterministic offline advisory
        assert advisory.is_advisory is True
        assert advisory.provider == "deterministic-offline-rule-engine"
