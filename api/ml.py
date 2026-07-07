import os
import joblib
from typing import Optional

BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "..", "ml", "saved_brain.pkl")
_model = None


def load_model() -> Optional[object]:
    global _model
    if _model is not None:
        return _model
    if not os.path.exists(MODEL_PATH):
        return None
    try:
        _model = joblib.load(MODEL_PATH)
        return _model
    except Exception:
        _model = None
        return None


def predict_category(description: str) -> str:
    model = load_model()
    if model is None:
        return "Uncategorized (No AI model found)"
    try:
        return model.predict([description])[0]
    except Exception:
        return "Uncategorized (Model Error)"
