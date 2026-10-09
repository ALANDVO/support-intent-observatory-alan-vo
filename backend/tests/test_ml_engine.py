"""Unit tests for ML engine: TF-IDF vectorization, training, and feature extraction."""

import pytest
from app.services.ml_engine import MLEngine


def test_ml_engine_insufficient_samples():
    engine = MLEngine(storage_dir="/tmp/test_models")
    with pytest.raises(ValueError, match="Insufficient training samples"):
        engine.train_and_evaluate(
            texts=["short text"] * 5,
            labels=["intent_a"] * 5,
            hyperparams={},
            model_id="test_fail_samples",
        )


def test_ml_engine_insufficient_classes():
    engine = MLEngine(storage_dir="/tmp/test_models")
    with pytest.raises(ValueError, match="At least 2 distinct classes"):
        engine.train_and_evaluate(
            texts=["Sample ticket number " + str(i) for i in range(15)],
            labels=["single_intent"] * 15,
            hyperparams={},
            model_id="test_fail_classes",
        )


def test_ml_engine_train_and_evaluate_success():
    engine = MLEngine(storage_dir="/tmp/test_models")
    texts = [
        "Please cancel my monthly subscription plan immediately",
        "How do I cancel our company recurring account?",
        "Terminate my subscription before the next renewal date",
        "I want to discontinue this enterprise service",
        "Cancel my account and delete all user records",
        "Why was my card billed twice this month?",
        "Where can I find our latest invoice PDF receipt?",
        "Payment failed with error card declined",
        "Need to update billing address on future statements",
        "Disputed charge on our credit card statement",
        "500 internal server error when uploading files",
        "API webhook endpoint returns 502 bad gateway",
        "UI dashboard crashes with unhandled TypeError",
        "Database sync latency is exceeding 15 seconds",
        "JSON payload parsing error in our webhook",
    ]
    labels = (
        ["cancellation"] * 5
        + ["billing_inquiry"] * 5
        + ["technical_issue"] * 5
    )
    hyperparams = {
        "ngram_min": 1,
        "ngram_max": 2,
        "c_regularization": 1.0,
        "test_size": 0.20,
    }

    result = engine.train_and_evaluate(
        texts=texts,
        labels=labels,
        hyperparams=hyperparams,
        model_id="test_model_1",
    )

    assert "overall_metrics" in result
    metrics = result["overall_metrics"]
    assert 0.0 <= metrics["accuracy"] <= 1.0
    assert 0.0 <= metrics["macro_f1"] <= 1.0

    assert "confusion_matrix" in result
    cm = result["confusion_matrix"]
    assert len(cm["labels"]) == 3
    assert len(cm["matrix"]) == 3
    assert len(cm["normalized_matrix"]) == 3

    assert "discriminative_features" in result
    feat = result["discriminative_features"]["per_intent_features"]
    assert "cancellation" in feat
    assert len(feat["cancellation"]) > 0

    assert "baseline_comparison" in result
    assert result["baseline_comparison"]["baseline_type"] == "majority_class_heuristic"


def test_ml_engine_predict_with_token_highlights():
    engine = MLEngine(storage_dir="/tmp/test_models")
    texts = [
        "cancel subscription plan immediately",
        "cancel recurring billing account",
        "cancel my team plan",
        "cancel contract right now",
        "cancel membership today",
        "why was my invoice billed twice",
        "need receipt for invoice payment",
        "card payment failed on invoice",
        "update billing email for invoice",
        "billing dispute on credit charge",
    ]
    labels = ["cancellation"] * 5 + ["billing_inquiry"] * 5
    engine.train_and_evaluate(
        texts=texts,
        labels=labels,
        hyperparams={"ngram_min": 1, "ngram_max": 1, "test_size": 0.2},
        model_id="test_model_2",
    )

    pred = engine.predict("I need to cancel my subscription")
    assert pred["predicted_intent"] == "cancellation"
    assert pred["confidence"] > 0.5
    assert pred["margin"] >= 0.0
    assert len(pred["candidates"]) == 2
    assert len(pred["token_highlights"]) > 0
    assert any(th["token"] == "cancel" for th in pred["token_highlights"])
