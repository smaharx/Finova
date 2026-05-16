import os
import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Initialize the API application
app = FastAPI(title="Finance Tracker API", version="2.0")

# Define the data structure we expect from the frontend
class Transaction(BaseModel):
    description: str

# Safely load the ML model
MODEL_PATH = os.path.join("ml", "saved_brain.pkl")
try:
    model = joblib.load(MODEL_PATH)
    MODEL_LOADED = True
except FileNotFoundError:
    model = None
    MODEL_LOADED = False

# 1. Health Check Endpoint
@app.get("/")
def health_check():
    return {
        "status": "online",
        "message": "FastAPI backend is running successfully.",
        "version": "2.0",
        "ai_model_loaded": MODEL_LOADED
    }

# 2. AI Prediction Endpoint (Uncommented and fixed)
@app.post("/predict")
def predict_category(item: Transaction):
    if not MODEL_LOADED:
        raise HTTPException(status_code=503, detail="AI Model is not loaded. Train the model first.")
    
    # Run the prediction
    prediction = model.predict([item.description])[0]
    return {
        "description": item.description, 
        "predicted_category": prediction
    }