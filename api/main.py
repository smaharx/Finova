from fastapi import FastAPI
from api.routers import transactions, corrections, analytics
from api.routers import ml as ml_router
from api.ml import load_model

app = FastAPI(title="Finance Tracker API", version="2.0")

# Eagerly load model into worker process (safe lazy load is in api/ml.py)
load_model()

app.include_router(transactions.router)
app.include_router(corrections.router)
app.include_router(analytics.router)
app.include_router(ml_router.router)

@app.get("/")
def health_check():
    from api.ml import load_model
    return {"status": "online", "message": "FastAPI backend is running successfully.", "version": "2.0", "ai_model_loaded": load_model() is not None}
