from fastapi import APIRouter
from api.ml import load_model

router = APIRouter(prefix="/ml", tags=["ml"])

@router.get("/info", response_model=dict)
def ml_info():
    model = load_model()
    return {
        "model_loaded": model is not None,
        "model_version": getattr(model, "version", None) if model is not None else None,
    }
