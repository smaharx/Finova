import argparse
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


DEFAULT_TRAIN_PATH = Path("data/synthetic_expenses.csv")
DEFAULT_MODEL_PATH = Path("ml/saved_brain.pkl")
DEFAULT_METRICS_JSON_PATH = Path("ml/evaluation_metrics.json")
DEFAULT_METRICS_TXT_PATH = Path("ml/evaluation_report.txt")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Evaluate Finova's category classifier."
    )
    parser.add_argument(
        "--train-data",
        type=Path,
        default=DEFAULT_TRAIN_PATH,
        help="Training dataset used to train the model if needed.",
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=None,
        help=(
            "Optional hard validation dataset. "
            "If provided, the entire file is used as the test set without splitting."
        ),
    )
    parser.add_argument(
        "--force-train",
        action="store_true",
        help="Force retraining even if a saved model already exists.",
    )
    return parser.parse_args()


def load_labeled_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    df = pd.read_csv(path)

    required_columns = {"Description", "Category"}
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")

    df = df.dropna(subset=["Description", "Category"]).copy()
    df["Description"] = df["Description"].astype(str)
    df["Category"] = df["Category"].astype(str)

    if df.empty:
        raise ValueError(f"Dataset is empty after cleaning: {path}")

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


def train_or_load_classifier(
    X_train, y_train, model_path: Path, force_train: bool = False
):
    if model_path.exists() and not force_train:
        print(f"Loading saved classifier from: {model_path}")
        return joblib.load(model_path)

    print("Saved model not found or retrain forced. Training a fresh classifier...")
    model = make_pipeline(
        TfidfVectorizer(ngram_range=(1, 2)),
        MultinomialNB(),
    )
    model.fit(X_train, y_train)

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    print(f"Model trained and saved to: {model_path}")

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


def save_metrics(results: dict, json_path: Path, txt_path: Path):
    json_path.parent.mkdir(parents=True, exist_ok=True)

    json_payload = {
        "accuracy": results["accuracy"],
        "precision_macro": results["precision_macro"],
        "recall_macro": results["recall_macro"],
        "f1_macro": results["f1_macro"],
        "confusion_matrix": results["confusion_matrix"],
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_payload, f, indent=2)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("=== Finova ML Evaluation Report ===\n\n")
        f.write(f"Accuracy: {results['accuracy']:.4f}\n")
        f.write(f"Precision (macro): {results['precision_macro']:.4f}\n")
        f.write(f"Recall (macro): {results['recall_macro']:.4f}\n")
        f.write(f"F1 Score (macro): {results['f1_macro']:.4f}\n\n")
        f.write("Classification Report:\n")
        f.write(results["classification_report"])
        f.write("\nConfusion Matrix:\n")
        f.write(str(results["confusion_matrix"]))

    print(f"Saved JSON metrics to: {json_path}")
    print(f"Saved text report to: {txt_path}")


def main():
    args = parse_args()

    print("Loading training dataset...")
    train_df = load_labeled_dataset(args.train_data)
    print(f"Loaded {len(train_df)} labeled rows from training data.")

    if args.data:
        print(f"Loading hard validation dataset: {args.data}")
        eval_df = load_labeled_dataset(args.data)
        print(f"Loaded {len(eval_df)} labeled rows for hard validation.")

        X_train = train_df["Description"]
        y_train = train_df["Category"]
        X_test = eval_df["Description"]
        y_test = eval_df["Category"]

        model = train_or_load_classifier(
            X_train=X_train,
            y_train=y_train,
            model_path=DEFAULT_MODEL_PATH,
            force_train=args.force_train,
        )

        metrics_suffix = f"_{args.data.stem}"
        json_path = Path(f"ml/evaluation_metrics{metrics_suffix}.json")
        txt_path = Path(f"ml/evaluation_report{metrics_suffix}.txt")

    else:
        X_train, X_test, y_train, y_test = split_dataset(train_df)
        print(f"Training rows: {len(X_train)}")
        print(f"Testing rows: {len(X_test)}")

        model = train_or_load_classifier(
            X_train=X_train,
            y_train=y_train,
            model_path=DEFAULT_MODEL_PATH,
            force_train=args.force_train,
        )

        json_path = DEFAULT_METRICS_JSON_PATH
        txt_path = DEFAULT_METRICS_TXT_PATH

    print("Evaluating model...")
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

    save_metrics(results, json_path=json_path, txt_path=txt_path)


if __name__ == "__main__":
    main()
