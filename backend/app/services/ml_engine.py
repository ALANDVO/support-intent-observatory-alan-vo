"""Local TF-IDF Intent Classification Engine."""

import os
import re
from typing import Any, Dict, List, Optional
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support, accuracy_score
from sklearn.model_selection import train_test_split


class IntentModelArtifact:
    def __init__(self, vectorizer: TfidfVectorizer, classifier: LogisticRegression, labels: List[str]):
        self.vectorizer = vectorizer
        self.classifier = classifier
        self.labels = sorted(labels)
        self.feature_names = vectorizer.get_feature_names_out()

    def predict_single(self, text: str) -> Dict[str, Any]:
        clean = text.strip()
        if not clean:
            return {"predicted_intent": "unknown", "confidence": 0.0, "margin": 0.0, "candidates": [], "token_highlights": []}

        vec = self.vectorizer.transform([clean])
        probabilities = self.classifier.predict_proba(vec)[0]

        class_probs = [
            {"intent": str(lbl), "probability": float(probabilities[idx])}
            for idx, lbl in enumerate(self.classifier.classes_)
        ]
        class_probs.sort(key=lambda x: x["probability"], reverse=True)

        top_1 = class_probs[0]
        top_2 = class_probs[1] if len(class_probs) > 1 else {"intent": "none", "probability": 0.0}
        margin = float(top_1["probability"] - top_2["probability"])
        highlights = self._extract_token_highlights(clean, top_1["intent"])

        return {
            "predicted_intent": top_1["intent"],
            "confidence": float(top_1["probability"]),
            "margin": margin,
            "candidates": class_probs,
            "token_highlights": highlights,
        }

    def _extract_token_highlights(self, text: str, target_intent: str) -> List[Dict[str, float]]:
        tokens = re.findall(r"\b[a-zA-Z]{2,}\b", text.lower())
        if not tokens or target_intent not in self.classifier.classes_:
            return []

        class_idx = list(self.classifier.classes_).index(target_intent)
        if len(self.classifier.classes_) == 2:
            coefs = -self.classifier.coef_[0] if class_idx == 0 else self.classifier.coef_[0]
        else:
            coefs = self.classifier.coef_[class_idx]
        feature_dict = {f: idx for idx, f in enumerate(self.feature_names)}

        highlights: Dict[str, float] = {}
        for tok in tokens:
            if tok in feature_dict:
                weight = float(coefs[feature_dict[tok]])
                if weight > 0:
                    highlights[tok] = max(highlights.get(tok, 0.0), round(weight, 4))

        sorted_tokens = sorted(highlights.items(), key=lambda x: x[1], reverse=True)[:6]
        return [{"token": t, "contribution": c} for t, c in sorted_tokens]


class MLEngine:
    def __init__(self, storage_dir: str = "./data/models"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        self.active_artifact: Optional[IntentModelArtifact] = None
        self.active_model_id: Optional[str] = None

    def train_and_evaluate(
        self,
        texts: List[str],
        labels: List[str],
        hyperparams: Dict[str, Any],
        model_id: str,
    ) -> Dict[str, Any]:
        if len(texts) < 10:
            raise ValueError(f"Insufficient training samples: {len(texts)} provided (minimum 10).")

        unique_labels = sorted(list(set(labels)))
        if len(unique_labels) < 2:
            raise ValueError(f"At least 2 distinct classes required; found {len(unique_labels)}.")

        test_size = float(hyperparams.get("test_size", 0.25))
        ngram_min = int(hyperparams.get("ngram_min", 1))
        ngram_max = int(hyperparams.get("ngram_max", 2))
        min_df = int(hyperparams.get("min_df", 1))
        max_df = float(hyperparams.get("max_df", 0.95))
        c_reg = float(hyperparams.get("c_regularization", 1.0))
        max_iter = int(hyperparams.get("max_iter", 500))

        class_counts = {l: labels.count(l) for l in unique_labels}
        stratify_arg = labels if all(c >= 2 for c in class_counts.values()) else None

        x_train, x_test, y_train, y_test = train_test_split(
            texts, labels, test_size=test_size, random_state=42, stratify=stratify_arg
        )

        vectorizer = TfidfVectorizer(
            ngram_range=(ngram_min, ngram_max),
            min_df=min_df,
            max_df=max_df,
            sublinear_tf=True,
            stop_words="english",
            norm="l2",
        )
        x_train_vec = vectorizer.fit_transform(x_train)
        x_test_vec = vectorizer.transform(x_test)

        classifier = LogisticRegression(C=c_reg, max_iter=max_iter, class_weight="balanced", random_state=42)
        classifier.fit(x_train_vec, y_train)

        y_pred = classifier.predict(x_test_vec)
        accuracy = float(accuracy_score(y_test, y_pred))
        precision_m, recall_m, f1_m, _ = precision_recall_fscore_support(y_test, y_pred, average="macro", zero_division=0)
        precision_w, recall_w, f1_w, _ = precision_recall_fscore_support(y_test, y_pred, average="weighted", zero_division=0)

        overall_metrics = {
            "accuracy": round(accuracy, 4),
            "macro_precision": round(float(precision_m), 4),
            "macro_recall": round(float(recall_m), 4),
            "macro_f1": round(float(f1_m), 4),
            "weighted_precision": round(float(precision_w), 4),
            "weighted_recall": round(float(recall_w), 4),
            "weighted_f1": round(float(f1_w), 4),
        }

        precision_pc, recall_pc, f1_pc, support_pc = precision_recall_fscore_support(
            y_test, y_pred, labels=unique_labels, average=None, zero_division=0
        )
        per_class_metrics = {
            lbl: {
                "precision": round(float(precision_pc[i]), 4),
                "recall": round(float(recall_pc[i]), 4),
                "f1_score": round(float(f1_pc[i]), 4),
                "support": int(support_pc[i]),
            }
            for i, lbl in enumerate(unique_labels)
        }

        cm = confusion_matrix(y_test, y_pred, labels=unique_labels)
        normalized_matrix = [
            [round(float(v) / r.sum(), 4) if r.sum() > 0 else 0.0 for v in r]
            for r in cm
        ]

        feature_names = vectorizer.get_feature_names_out()
        per_intent_features: Dict[str, List[Dict[str, Any]]] = {}
        for c_idx, lbl in enumerate(classifier.classes_):
            if len(classifier.classes_) == 2:
                coefs = -classifier.coef_[0] if c_idx == 0 else classifier.coef_[0]
            else:
                coefs = classifier.coef_[c_idx]
            top_indices = np.argsort(coefs)[::-1][:8]
            per_intent_features[str(lbl)] = [
                {"feature": str(feature_names[i]), "weight": round(float(coefs[i]), 4)}
                for i in top_indices
            ]

        majority_count = max(class_counts.values())
        baseline_acc = round(float(majority_count) / len(labels), 4)
        acc_delta = round(accuracy - baseline_acc, 4)

        artifact = IntentModelArtifact(vectorizer, classifier, unique_labels)
        artifact_path = os.path.join(self.storage_dir, f"model_{model_id}.joblib")
        joblib.dump(artifact, artifact_path)

        self.active_artifact = artifact
        self.active_model_id = model_id

        return {
            "overall_metrics": overall_metrics,
            "per_class_metrics": per_class_metrics,
            "confusion_matrix": {"labels": unique_labels, "matrix": cm.tolist(), "normalized_matrix": normalized_matrix},
            "discriminative_features": {"per_intent_features": per_intent_features},
            "baseline_comparison": {
                "baseline_type": "majority_class_heuristic",
                "baseline_accuracy": baseline_acc,
                "model_accuracy": round(accuracy, 4),
                "accuracy_delta": acc_delta,
                "interpretation": f"TF-IDF model outperforms baseline by {round(acc_delta * 100, 2)}% across {len(unique_labels)} classes.",
            },
            "train_sample_count": len(x_train),
            "test_sample_count": len(x_test),
            "model_file_path": artifact_path,
        }

    def load_model(self, model_id: str, file_path: str) -> bool:
        if not os.path.exists(file_path):
            return False
        try:
            self.active_artifact = joblib.load(file_path)
            self.active_model_id = model_id
            return True
        except Exception:
            return False

    def predict(self, text: str) -> Dict[str, Any]:
        if not self.active_artifact:
            return {"predicted_intent": "unclassified", "confidence": 0.0, "margin": 0.0, "candidates": [], "token_highlights": []}
        return self.active_artifact.predict_single(text)


ml_engine = MLEngine()
