import os
import joblib
from typing import Optional

BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "saved_brain.pkl")

_model = None


def _load_model() -> Optional[object]:
    global _model
    if _model is not None:
        return _model

    if not os.path.exists(MODEL_PATH):
        return None

    try:
        _model = joblib.load(MODEL_PATH)
        return _model
    except Exception:
        # Don't crash import if model file is corrupted; return None and let callers handle it.
        _model = None
        return None


def predict_category(description: str) -> str:
    """
    Predict the category for a single transaction description.
    Returns a string category or a human-readable "Uncategorized (...)" message
    when the model is not available.
    """
    model = _load_model()
    if model is None:
        return "Uncategorized (No AI model found)"

    try:
        return model.predict([description])[0]
    except Exception:
        return "Uncategorized (Model Error)"


if __name__ == "__main__":
    samples = [
        "UBER RIDES SF",
        "AMZN MKTP US #9923",
        "CITY APARTMENTS LEASING"
    ]
    for s in samples:
        print(f"'{s}' -> {predict_category(s)}")
