"""LLM advisory service supporting OpenAI-compatible, Anthropic, Gemini, and Ollama."""

import json
import re
from typing import Optional
import httpx
from app.core.config import settings
from app.models.schemas import AdvisoryResponse


class LLMService:
    def __init__(self):
        self.timeout = settings.llm_timeout_seconds

    def generate_advisory(
        self,
        ticket_text: str,
        predicted_intent: str,
        confidence: float,
        is_uncertain: bool,
    ) -> AdvisoryResponse:
        api_key = settings.llm_api_key
        provider = (settings.llm_provider or "openai-compatible").lower()
        model = settings.llm_model or "default-model"

        if not api_key and provider != "ollama":
            return self._generate_offline_advisory(ticket_text, predicted_intent, confidence, is_uncertain)

        try:
            if provider == "anthropic":
                return self._call_anthropic(ticket_text, predicted_intent, confidence, is_uncertain, api_key, model)
            elif provider == "gemini":
                return self._call_gemini(ticket_text, predicted_intent, confidence, is_uncertain, api_key, model)
            elif provider == "ollama":
                return self._call_ollama(ticket_text, predicted_intent, confidence, is_uncertain, model)
            else:
                return self._call_openai(ticket_text, predicted_intent, confidence, is_uncertain, api_key, model)
        except Exception:
            return self._generate_offline_advisory(ticket_text, predicted_intent, confidence, is_uncertain)

    def _generate_offline_advisory(
        self,
        ticket_text: str,
        predicted_intent: str,
        confidence: float,
        is_uncertain: bool,
    ) -> AdvisoryResponse:
        words = re.findall(r"\b[a-zA-Z]{3,}\b", ticket_text.lower())
        key_signals = list(dict.fromkeys(words))[:4]
        risk = "high" if (is_uncertain and confidence < 0.4) else ("medium" if is_uncertain else "low")

        if is_uncertain:
            action = f"Flagged for operator review (confidence: {confidence:.1%}). Verify customer goal."
        else:
            action = f"Route directly to {predicted_intent.replace('_', ' ').title()} tier."

        responses = {
            "billing_inquiry": "We are reviewing your invoice statement and will respond shortly.",
            "account_access": "We received your account access inquiry and are verifying your credentials.",
            "technical_issue": "Our technical team has logged this issue and is inspecting service logs.",
            "feature_request": "Thank you for the enhancement feedback. We cataloged this for our roadmap.",
            "cancellation": "We received your cancellation request and are preparing details on your term.",
            "refund_request": "We received your refund inquiry. Our finance specialist is reviewing records.",
        }
        draft = responses.get(predicted_intent, "Thank you for reaching out to customer support.")

        return AdvisoryResponse(
            summary=f"Inquiry classified as '{predicted_intent}' with {confidence:.1%} confidence.",
            suggested_action=action,
            key_signals=key_signals,
            risk_assessment=risk,
            draft_response=f"Hello,\n\n{draft}\n\nBest regards,\nCustomer Support Operations",
            is_advisory=True,
            provider="deterministic-offline-rule-engine",
            model="offline-nlp-heuristics",
        )

    def _call_openai(self, text, intent, conf, uncertain, key, model):
        url = (settings.llm_base_url or "https://api.openai.com/v1").rstrip("/") + "/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a customer support triage assistant. Respond in JSON."},
                {"role": "user", "content": f"Ticket: {text}\nIntent: {intent} (Conf: {conf:.2f})\nReturn JSON: summary, suggested_action, key_signals, risk_assessment, draft_response."},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, headers={"Authorization": f"Bearer {key}"}, json=payload)
            resp.raise_for_status()
            p = json.loads(resp.json()["choices"][0]["message"]["content"])
            return AdvisoryResponse(
                summary=p.get("summary", "Analysis complete."),
                suggested_action=p.get("suggested_action", "Review ticket."),
                key_signals=p.get("key_signals", []),
                risk_assessment=p.get("risk_assessment", "medium"),
                draft_response=p.get("draft_response", "Thank you for reaching out."),
                is_advisory=True,
                provider="openai-compatible",
                model=model,
            )

    def _call_anthropic(self, text, intent, conf, uncertain, key, model):
        url = (settings.llm_base_url or "https://api.anthropic.com").rstrip("/") + "/v1/messages"
        headers = {"x-api-key": key or "", "anthropic-version": "2023-06-01"}
        prompt = f"Analyze: {text}. Intent: {intent}. Return JSON: {{\"summary\":\"...\",\"suggested_action\":\"...\",\"key_signals\":[],\"risk_assessment\":\"low|med|high\",\"draft_response\":\"...\"}}"
        payload = {"model": model, "max_tokens": 1000, "messages": [{"role": "user", "content": prompt}]}
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            p = json.loads(resp.json()["content"][0]["text"])
            return AdvisoryResponse(
                summary=p.get("summary", "Analysis complete."),
                suggested_action=p.get("suggested_action", "Review ticket."),
                key_signals=p.get("key_signals", []),
                risk_assessment=p.get("risk_assessment", "medium"),
                draft_response=p.get("draft_response", "Thank you for contacting us."),
                is_advisory=True,
                provider="anthropic",
                model=model,
            )

    def _call_gemini(self, text, intent, conf, uncertain, key, model):
        url = f"{(settings.llm_base_url or 'https://generativelanguage.googleapis.com').rstrip('/')}/v1beta/models/{model}:generateContent?key={key}"
        prompt = f"Analyze ticket: {text}. Predicted: {intent}. Return JSON: summary, suggested_action, key_signals, risk_assessment, draft_response."
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            clean = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE)
            p = json.loads(clean)
            return AdvisoryResponse(
                summary=p.get("summary", "Analysis complete."),
                suggested_action=p.get("suggested_action", "Review ticket."),
                key_signals=p.get("key_signals", []),
                risk_assessment=p.get("risk_assessment", "medium"),
                draft_response=p.get("draft_response", "Thank you for contacting us."),
                is_advisory=True,
                provider="gemini",
                model=model,
            )

    def _call_ollama(self, text, intent, conf, uncertain, model):
        url = (settings.llm_base_url or "http://127.0.0.1:11434").rstrip("/") + "/api/chat"
        prompt = f"Ticket: {text}. Intent: {intent}. Return JSON with summary, suggested_action, key_signals, risk_assessment, draft_response."
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "format": "json", "stream": False}
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            p = json.loads(resp.json()["message"]["content"])
            return AdvisoryResponse(
                summary=p.get("summary", "Analysis complete."),
                suggested_action=p.get("suggested_action", "Review ticket."),
                key_signals=p.get("key_signals", []),
                risk_assessment=p.get("risk_assessment", "medium"),
                draft_response=p.get("draft_response", "Thank you for contacting us."),
                is_advisory=True,
                provider="ollama",
                model=model,
            )


llm_service = LLMService()
