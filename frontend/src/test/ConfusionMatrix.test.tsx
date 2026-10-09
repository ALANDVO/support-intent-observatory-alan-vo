import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ConfusionMatrix } from "../components/ConfusionMatrix";
import { EvaluationData } from "../types/api";

describe("ConfusionMatrix Component", () => {
  const mockEval: EvaluationData = {
    id: "eval-001",
    model_id: "mod-001",
    overall_metrics: {
      accuracy: 0.9,
      macro_precision: 0.88,
      macro_recall: 0.89,
      macro_f1: 0.885,
      weighted_precision: 0.9,
      weighted_recall: 0.9,
      weighted_f1: 0.9,
    },
    per_class_metrics: {
      billing_inquiry: { precision: 0.92, recall: 0.9, f1_score: 0.91, support: 10 },
      cancellation: { precision: 0.85, recall: 0.88, f1_score: 0.86, support: 10 },
    },
    confusion_matrix: {
      labels: ["billing_inquiry", "cancellation"],
      matrix: [
        [9, 1],
        [1, 9],
      ],
      normalized_matrix: [
        [0.9, 0.1],
        [0.1, 0.9],
      ],
    },
    discriminative_features: {
      per_intent_features: {
        billing_inquiry: [{ feature: "invoice", weight: 2.1 }],
        cancellation: [{ feature: "cancel", weight: 2.4 }],
      },
    },
    baseline_comparison: {
      baseline_type: "majority_class_heuristic",
      baseline_accuracy: 0.5,
      model_accuracy: 0.9,
      accuracy_delta: 0.4,
      interpretation: "TF-IDF model outperforms naive baseline by 40.0% across 2 intent classes.",
    },
    created_at: new Date().toISOString(),
  };

  it("renders baseline comparison and per-class metrics", () => {
    render(<ConfusionMatrix evaluation={mockEval} isLoading={false} />);

    expect(
      screen.getByText("TF-IDF model outperforms naive baseline by 40.0% across 2 intent classes.")
    ).toBeInTheDocument();
    expect(screen.getByText("Lift: +40.0%")).toBeInTheDocument();
    expect(screen.getAllByText("billing inquiry").length).toBeGreaterThan(0);
    expect(screen.getAllByText("cancellation").length).toBeGreaterThan(0);
    expect(screen.getByText("invoice")).toBeInTheDocument();
    expect(screen.getByText("cancel")).toBeInTheDocument();
  });

  it("selects confusion matrix cell on click", () => {
    render(<ConfusionMatrix evaluation={mockEval} isLoading={false} />);

    const cells = screen.getAllByText("9");
    expect(cells.length).toBeGreaterThan(0);
    fireEvent.click(cells[0]);

    expect(screen.getByText("Selected:")).toBeInTheDocument();
  });
});
