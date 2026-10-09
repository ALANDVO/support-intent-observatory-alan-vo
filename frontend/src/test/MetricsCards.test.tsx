import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MetricsCards } from "../components/MetricsCards";
import { SystemStats } from "../types/api";

describe("MetricsCards Component", () => {
  const mockStats: SystemStats = {
    dataset_count: 2,
    ticket_count: 120,
    model_count: 3,
    pending_review_count: 5,
    resolved_review_count: 14,
    active_model_name: "prod_tfidf_classifier",
    active_model_accuracy: 0.9333,
    active_model_macro_f1: 0.925,
  };

  it("renders active model name and metrics correctly", () => {
    const onNavigate = vi.fn();
    render(<MetricsCards stats={mockStats} onNavigateToReview={onNavigate} />);

    expect(screen.getByText("prod_tfidf_classifier")).toBeInTheDocument();
    expect(screen.getByText("93.3%")).toBeInTheDocument();
    expect(screen.getByText("92.5%")).toBeInTheDocument();
    expect(screen.getByText("120")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
  });

  it("triggers onNavigateToReview callback when review card is clicked", () => {
    const onNavigate = vi.fn();
    render(<MetricsCards stats={mockStats} onNavigateToReview={onNavigate} />);

    const reviewCard = screen.getByText("Uncertain Review Queue").closest("div");
    if (reviewCard) {
      fireEvent.click(reviewCard);
      expect(onNavigate).toHaveBeenCalled();
    }
  });
});
