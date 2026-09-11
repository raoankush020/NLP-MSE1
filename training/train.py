import os
import csv
from pathlib import Path
import numpy as np
import joblib
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.base import BaseEstimator, TransformerMixin

class PairFeatureExtractor(BaseEstimator, TransformerMixin):
    """Computes interaction features between context and claim."""
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        features = []
        for text in X:
            # text is formatted as "{claim} [SEP] {context}"
            parts = text.split(" [SEP] ")
            claim = parts[0] if len(parts) > 0 else ""
            context = parts[1] if len(parts) > 1 else ""

            claim_words = set(claim.lower().split())
            ctx_words = set(context.lower().split())

            overlap = len(claim_words.intersection(ctx_words))
            jaccard = overlap / max(1, len(claim_words.union(ctx_words)))
            containment = overlap / max(1, len(claim_words))
            len_ratio = len(claim) / max(1, len(context))

            features.append([containment, jaccard, len_ratio])
        return np.array(features)

def load_data(csv_path: str):
    X_texts = []
    y_labels = []
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            claim = row["claim"].strip()
            context = row["context"].strip()
            label = int(row["label"].strip())
            # Format combined text for pipeline
            X_texts.append(f"{claim} [SEP] {context}")
            y_labels.append(label)
    return X_texts, np.array(y_labels)

def train_model():
    base_dir = Path(__file__).resolve().parent
    dataset_file = base_dir / "dataset.csv"
    model_dir = base_dir / "model"
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "classifier.joblib"

    print(f"Loading dataset from {dataset_file}...")
    X, y = load_data(str(dataset_file))
    print(f"Total samples: {len(X)}")

    # Split dataset
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

    # Build scikit-learn feature pipeline
    feature_union = FeatureUnion([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=1000)),
        ("overlap_stats", PairFeatureExtractor())
    ])

    pipeline = Pipeline([
        ("features", feature_union),
        ("clf", LogisticRegression(C=1.0, max_iter=200, random_state=42))
    ])

    print("Training classifier...")
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Test Accuracy: {acc:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["GROUNDED (0)", "HALLUCINATED (1)"]))

    # Re-train on full dataset for final deployment
    print("Fitting model on complete dataset...")
    pipeline.fit(X, y)

    joblib.dump(pipeline, model_path)
    print(f"Model saved successfully to {model_path}")

if __name__ == "__main__":
    train_model()
