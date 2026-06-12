import os
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline


DATA_PATH = Path("data/synthetic_expenses.csv")
MODEL_PATH = Path("ml/saved_brain.pkl")
METRICS_JSON_PATH = Path("ml/evaluation_metrics.json")
METRICS_TXT_PATH = Path("ml/evaluation_report.txt")


def load_labeled_dataset() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Labeled dataset not found at: {DATA_PATH}. "
            "Create it first or point the script to the correct CSV."
        )

    df = pd.read_csv(DATA_PATH)

    required_columns = {"Description", "Category"}
    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")

    df = df.dropna(subset=["Description", "Category"]).copy()
    df["Description"] = df["Description"].astype(str)
    df["Category"] = df["Category"].astype(str)

    if df.empty:
        raise ValueError("Dataset is empty after cleaning.")

    return df


def split_dataset(df: pd.DataFrame):
    X = df["Description"]
    y = df["Category"]

    return train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y if y.nunique() > 1 else None,
    )


def train_or_load_classifier(X_train, y_train):
    if MODEL_PATH.exists():
        print(f"Loading saved classifier from: {MODEL_PATH}")
        return joblib.load(MODEL_PATH)

    print("Saved model not found. Training a fresh classifier...")
    model = make_pipeline(
        TfidfVectorizer(ngram_range=(1, 2)),
        MultinomialNB(),
    )
    model.fit(X_train, y_train)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"Model trained and saved to: {MODEL_PATH}")

    return model


def evaluate_model(model, X_test, y_test):
    y_pred = model.predict(X_test)

    results = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision_macro": precision_score(
            y_test, y_pred, average="macro", zero_division=0
        ),
        "recall_macro": recall_score(y_test, y_pred, average="macro", zero_division=0),
        "f1_macro": f1_score(y_test, y_pred, average="macro", zero_division=0),
        "classification_report": classification_report(y_test, y_pred, zero_division=0),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
    }

    return results


def save_metrics(results: dict):
    METRICS_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)

    json_payload = {
        "accuracy": results["accuracy"],
        "precision_macro": results["precision_macro"],
        "recall_macro": results["recall_macro"],
        "f1_macro": results["f1_macro"],
        "confusion_matrix": results["confusion_matrix"],
    }

    with open(METRICS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(json_payload, f, indent=2)

    with open(METRICS_TXT_PATH, "w", encoding="utf-8") as f:
        f.write("=== Finova ML Evaluation Report ===\n\n")
        f.write(f"Accuracy: {results['accuracy']:.4f}\n")
        f.write(f"Precision (macro): {results['precision_macro']:.4f}\n")
        f.write(f"Recall (macro): {results['recall_macro']:.4f}\n")
        f.write(f"F1 Score (macro): {results['f1_macro']:.4f}\n\n")
        f.write("Classification Report:\n")
        f.write(results["classification_report"])
        f.write("\nConfusion Matrix:\n")
        f.write(str(results["confusion_matrix"]))

    print(f"Saved JSON metrics to: {METRICS_JSON_PATH}")
    print(f"Saved text report to: {METRICS_TXT_PATH}")


def main():
    print("Loading labeled dataset...")
    df = load_labeled_dataset()

    print(f"Loaded {len(df)} labeled rows.")
    X_train, X_test, y_train, y_test = split_dataset(df)

    print(f"Training rows: {len(X_train)}")
    print(f"Testing rows: {len(X_test)}")

    model = train_or_load_classifier(X_train, y_train)

    print("Evaluating model on test set...")
    results = evaluate_model(model, X_test, y_test)

    print("\n=== Evaluation Metrics ===")
    print(f"Accuracy: {results['accuracy']:.4f}")
    print(f"Precision (macro): {results['precision_macro']:.4f}")
    print(f"Recall (macro): {results['recall_macro']:.4f}")
    print(f"F1 Score (macro): {results['f1_macro']:.4f}")

    print("\n=== Classification Report ===")
    print(results["classification_report"])

    print("=== Confusion Matrix ===")
    print(results["confusion_matrix"])

    save_metrics(results)


if __name__ == "__main__":
    main()
