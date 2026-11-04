import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ThresholdOptimization from "../components/ThresholdOptimization";
import { api } from "../api/client";

describe("ThresholdOptimization Component", () => {
  it("fetches active model and runs threshold optimization", async () => {
    vi.spyOn(api, "listModels").mockResolvedValueOnce([
      { id: "model-1", name: "Test Model", version: 1, status: "ready", accuracy: 0.85, is_active: true, hyperparameters: {}, dataset_id: "ds-1", created_at: "2024-01-01T00:00:00Z" },
    ]);
    vi.spyOn(api, "optimizeThresholds").mockResolvedValueOnce({
      optimal_confidence_threshold: 0.725,
      optimal_margin_threshold: 0.15,
      expected_auto_routed_rate: 0.68,
      expected_auto_routed_accuracy: 0.91,
      expected_review_queue_rate: 0.32,
      threshold_curve: [
        { confidence_threshold: 0.725, margin_threshold: 0.15, auto_routed_rate: 0.68, auto_routed_accuracy: 0.91, review_queue_rate: 0.32, score: 0.619 },
        { confidence_threshold: 0.75, margin_threshold: 0.15, auto_routed_rate: 0.62, auto_routed_accuracy: 0.92, review_queue_rate: 0.38, score: 0.570 },
      ],
    });

    render(<ThresholdOptimization />);

    await waitFor(() => {
      const button = screen.getByRole("button", { name: /Optimize Thresholds/i });
      expect(button).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /Optimize Thresholds/i }));

    await waitFor(() => {
      expect(screen.getByText("Optimal Confidence Threshold")).toBeInTheDocument();
      expect(screen.getByText("Optimal Margin Threshold")).toBeInTheDocument();
      expect(screen.getByText("Expected Auto-Route Rate")).toBeInTheDocument();
      expect(screen.getByText("Expected Auto-Route Accuracy")).toBeInTheDocument();
      expect(screen.getByText("Expected Review Queue Rate")).toBeInTheDocument();
    });
  });

  it("shows message when no model is available", async () => {
    vi.spyOn(api, "listModels").mockResolvedValueOnce([]);

    render(<ThresholdOptimization />);

    await waitFor(() => {
      expect(screen.getByText("No trained model found. Train a model first in the Datasets & Training tab.")).toBeInTheDocument();
    });
  });
});
