import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { TriageWorkbench } from "../components/TriageWorkbench";
import { api } from "../api/client";

describe("TriageWorkbench Component", () => {
  it("submits ticket triage and displays model prediction", async () => {
    vi.spyOn(api, "triageTicket").mockResolvedValueOnce({
      ticket_id: "tkt-001",
      text: "I want to cancel my team subscription plan",
      predicted_intent: "cancellation",
      confidence: 0.942,
      margin: 0.81,
      is_uncertain: false,
      uncertainty_reason: null,
      routing_status: "auto_routed",
      candidates: [
        { intent: "cancellation", probability: 0.942 },
        { intent: "refund_request", probability: 0.035 },
      ],
      token_highlights: [{ token: "cancel", contribution: 2.15 }],
      advisory: {
        summary: "Inquiry classified as cancellation with high confidence.",
        suggested_action: "Route to subscription cancellation playbook.",
        key_signals: ["cancel", "subscription", "plan"],
        risk_assessment: "low",
        draft_response: "Hello, we are processing your cancellation request.",
        is_advisory: true,
        provider: "deterministic-offline-rule-engine",
        model: "offline-nlp-heuristics",
      },
    });

    render(<TriageWorkbench />);

    const textarea = screen.getByPlaceholderText("Paste customer support inquiry or message...");
    fireEvent.change(textarea, {
      target: { value: "I want to cancel my team subscription plan" },
    });

    const button = screen.getByRole("button", { name: /Triage Ticket/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getAllByText("cancellation").length).toBeGreaterThan(0);
      expect(screen.getAllByText(/94\.2/).length).toBeGreaterThan(0);
      expect(screen.getByText(/Confident Prediction/i)).toBeInTheDocument();
      expect(screen.getByText("cancel")).toBeInTheDocument();
      expect(screen.getByText("Route to subscription cancellation playbook.")).toBeInTheDocument();
    });
  });
});
