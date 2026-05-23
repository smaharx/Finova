import os
import joblib
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func # Add this


# Import our custom database configurations and models
from api.database import get_db
from api.models import TransactionModel

# Initialize the API application
app = FastAPI(title="Finance Tracker API", version="2.0")

# Define the data structure we expect from the frontend for AI classification
class TransactionCreate(BaseModel):
    description: str

# Safely load the ML model
MODEL_PATH = os.path.join("ml", "saved_brain.pkl")
try:
    model = joblib.load(MODEL_PATH)
    MODEL_LOADED = True
except FileNotFoundError:
    model = None
    MODEL_LOADED = False


# ==========================================
# ENDPOINT 1: SERVICE HEALTH CHECK
# ==========================================
@app.get("/")
def health_check():
    return {
        "status": "online",
        "message": "FastAPI backend is running successfully.",
        "version": "2.0",
        "ai_model_loaded": MODEL_LOADED
    }


# ==========================================
# ENDPOINT 2: AI CATEGORY INFERENCE
# ==========================================
@app.post("/predict")
def predict_category(item: TransactionCreate):
    if not MODEL_LOADED:
        raise HTTPException(status_code=503, detail="AI Model is not loaded. Train the model first.")
    
    prediction = model.predict([item.description])[0]
    return {
        "description": item.description, 
        "predicted_category": prediction
    }



# ==========================================
# ENDPOINT 3: REFRACTORED ORM DATA FETCHING
# ==========================================
@app.get("/transactions")
def get_transactions(limit: int = 50, db: Session = Depends(get_db)):
    """
    Fetches the most recent transactions using SQLAlchemy ORM expressions.
    Injects the database session using FastAPI's dependency injection system.
    """
    try:
        # We query the database using the Python Class instead of hardcoded SQL strings
        transactions = db.query(TransactionModel).order_by(TransactionModel.date.desc()).limit(limit).all()
        
        # Serialize the SQLAlchemy objects into a clean JSON structure
        serialized_transactions = [
            {
                "id": t.id,
                "date": t.date,
                "description": t.description,
                "category": t.category,
                "amount": t.amount,
                "is_anomaly": t.is_anomaly
            }
            for t in transactions
        ]
        
        return {"count": len(serialized_transactions), "transactions": serialized_transactions}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database abstraction layer error: {str(e)}")
    
    

# ==========================================
# ENDPOINT 4: CREATE AND CACHE TRANSACTION
# ==========================================
# We create a new Pydantic schema specifically for incoming transaction entries
class TransactionCreateInput(BaseModel):
    date: str
    description: str
    amount: float


@app.post("/transactions")
def create_transaction(item: TransactionCreateInput, db: Session = Depends(get_db)):
    """
    Accepts a new transaction, uses the internal AI model to predict its category,
    and commits the enriched record directly into the cloud PostgreSQL database.
    """
    # 1. Fallback if the AI model failed to load
    if MODEL_LOADED:
        predicted_cat = model.predict([item.description])[0]
    else:
        predicted_cat = "Uncategorized (Model Offline)"
        
    try:
        # 2. Map the input and AI prediction into our SQLAlchemy relational model
        new_record = TransactionModel(
            date=item.date,
            description=item.description,
            amount=item.amount,
            category=predicted_cat,
            is_anomaly=0 # Default to normal; anomaly engine comes in Streak 3
        )
        
        # 3. Use the ORM session to add and commit the record to the cloud network
        db.add(new_record)
        db.commit()
        db.refresh(new_record) # Pull back the auto-generated database ID
        
        return {
            "message": "Transaction successfully committed to cloud database.",
            "data": {
                "id": new_record.id,
                "date": new_record.date,
                "description": new_record.description,
                "category": new_record.category,
                "amount": new_record.amount
            }
        }
    except Exception as e:
        db.rollback() # Rollback the database state if the network connection drops mid-flight
        raise HTTPException(status_code=500, detail=f"Cloud write failure: {str(e)}")    

# ==========================================
# ENDPOINT 5: FINANCIAL ANALYTICS SUMMARY
# ==========================================
@app.get("/analytics/summary")
def get_analytics_summary(db: Session = Depends(get_db)):
    """
    Performs server-side aggregation to provide financial insights.
    Calculates total spending and breaks it down by category.
    """
    try:
        # 1. Calculate Total Spending across all transactions
        total_spent = db.query(func.sum(TransactionModel.amount)).scalar() or 0.0
        
        # 2. Calculate count of transactions
        total_count = db.query(func.count(TransactionModel.id)).scalar() or 0
        
        # 3. Categorical Breakdown (The heavy lifting)
        # SQL equivalent: SELECT category, SUM(amount) FROM transactions GROUP BY category
        category_data = db.query(
            TransactionModel.category, 
            func.sum(TransactionModel.amount).label("total_amount"),
            func.count(TransactionModel.id).label("count")
        ).group_by(TransactionModel.category).all()
        
        # Format the categorical data into a clean list of dictionaries
        breakdown = [
            {
                "category": row.category,
                "total_amount": row.total_amount,
                "transaction_count": row.count,
                "percentage": round((row.total_amount / total_spent) * 100, 2) if total_spent > 0 else 0
            }
            for row in category_data
        ]
        
        return {
            "overall": {
                "total_spent": round(total_spent, 2),
                "transaction_count": total_count,
            },
            "categorical_breakdown": breakdown
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics Engine Error: {str(e)}")    