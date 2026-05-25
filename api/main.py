import os
import statistics
import joblib
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from api.database import get_db
from api.models import TransactionModel, TransactionCorrectionModel

app = FastAPI(title="Finance Tracker API", version="2.0")


class TransactionCreate(BaseModel):
    description: str


class TransactionCreateInput(BaseModel):
    date: str
    description: str
    amount: float


class TransactionUpdateInput(BaseModel):
    date: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[str] = None


class TransactionCorrectionInput(BaseModel):
    corrected_category: str
    notes: Optional[str] = None


MODEL_PATH = os.path.join("ml", "saved_brain.pkl")
try:
    model = joblib.load(MODEL_PATH)
    MODEL_LOADED = True
except FileNotFoundError:
    model = None
    MODEL_LOADED = False


def predict_transaction_category(description: str) -> str:
    if MODEL_LOADED:
        return model.predict([description])[0]
    return "Uncategorized (Model Offline)"


def check_for_anomaly(db: Session, category: str, new_amount: float, exclude_id: Optional[int] = None):
    history_query = db.query(TransactionModel.amount).filter(TransactionModel.category == category)

    if exclude_id is not None:
        history_query = history_query.filter(TransactionModel.id != exclude_id)

    history = history_query.order_by(TransactionModel.id.desc()).limit(20).all()

    if len(history) < 5:
        return 0

    amounts = [h[0] for h in history]
    mean = statistics.mean(amounts)
    std_dev = statistics.stdev(amounts)

    if std_dev == 0:
        return 0

    z_score = abs(new_amount - mean) / std_dev
    return 1 if z_score > 3 else 0


def build_transaction_query(
    db: Session,
    search: Optional[str] = None,
    category: Optional[str] = None,
    only_anomalies: bool = False,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    query = db.query(TransactionModel)

    if search:
        query = query.filter(TransactionModel.description.ilike(f"%{search.strip()}%"))

    if category and category != "All":
        query = query.filter(TransactionModel.category == category)

    if only_anomalies:
        query = query.filter(TransactionModel.is_anomaly == 1)

    if start_date:
        query = query.filter(TransactionModel.date >= start_date)

    if end_date:
        query = query.filter(TransactionModel.date <= end_date)

    return query


@app.get("/")
def health_check():
    return {
        "status": "online",
        "message": "FastAPI backend is running successfully.",
        "version": "2.0",
        "ai_model_loaded": MODEL_LOADED,
    }


@app.post("/predict")
def predict_category(item: TransactionCreate):
    if not MODEL_LOADED:
        raise HTTPException(status_code=503, detail="AI Model is not loaded. Train the model first.")

    prediction = model.predict([item.description])[0]
    return {
        "description": item.description,
        "predicted_category": prediction,
    }


@app.get("/transactions")
def get_transactions(
    limit: int = 50,
    search: Optional[str] = None,
    category: Optional[str] = None,
    only_anomalies: bool = False,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
):
    try:
        query = build_transaction_query(
            db=db,
            search=search,
            category=category,
            only_anomalies=only_anomalies,
            start_date=start_date,
            end_date=end_date,
        )

        transactions = query.order_by(TransactionModel.date.desc()).limit(limit).all()

        serialized_transactions = [
            {
                "id": t.id,
                "date": t.date,
                "description": t.description,
                "category": t.category,
                "amount": t.amount,
                "is_anomaly": t.is_anomaly,
            }
            for t in transactions
        ]

        return {"count": len(serialized_transactions), "transactions": serialized_transactions}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database abstraction layer error: {str(e)}")


@app.post("/transactions")
def create_transaction(item: TransactionCreateInput, db: Session = Depends(get_db)):
    predicted_cat = predict_transaction_category(item.description)
    anomaly_status = check_for_anomaly(db, predicted_cat, item.amount)

    try:
        new_record = TransactionModel(
            date=item.date,
            description=item.description,
            amount=item.amount,
            category=predicted_cat,
            is_anomaly=anomaly_status,
        )

        db.add(new_record)
        db.commit()
        db.refresh(new_record)

        return {
            "message": "Transaction successfully committed to cloud database.",
            "data": {
                "id": new_record.id,
                "date": new_record.date,
                "description": new_record.description,
                "category": new_record.category,
                "amount": new_record.amount,
                "is_anomaly": new_record.is_anomaly,
            },
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Cloud write failure: {str(e)}")


@app.put("/transactions/{transaction_id}")
def update_transaction(
    transaction_id: int,
    item: TransactionUpdateInput,
    db: Session = Depends(get_db),
):
    record = db.query(TransactionModel).filter(TransactionModel.id == transaction_id).first()

    if not record:
        raise HTTPException(status_code=404, detail="Transaction not found")

    try:
        if item.date is not None:
            record.date = item.date

        if item.description is not None:
            clean_description = item.description.strip()
            if not clean_description:
                raise HTTPException(status_code=400, detail="Description cannot be empty.")
            record.description = clean_description

        if item.amount is not None:
            if item.amount <= 0:
                raise HTTPException(status_code=400, detail="Amount must be greater than zero.")
            record.amount = item.amount

        if item.category is not None:
            clean_category = item.category.strip()
            if not clean_category:
                raise HTTPException(status_code=400, detail="Category cannot be empty.")
            record.category = clean_category
        elif item.description is not None:
            record.category = predict_transaction_category(record.description)

        record.is_anomaly = check_for_anomaly(
            db,
            record.category,
            record.amount,
            exclude_id=record.id,
        )

        db.commit()
        db.refresh(record)

        return {
            "message": "Transaction updated successfully.",
            "data": {
                "id": record.id,
                "date": record.date,
                "description": record.description,
                "category": record.category,
                "amount": record.amount,
                "is_anomaly": record.is_anomaly,
            },
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


@app.delete("/transactions/{transaction_id}")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    record = db.query(TransactionModel).filter(TransactionModel.id == transaction_id).first()

    if not record:
        raise HTTPException(status_code=404, detail="Transaction not found")

    try:
        db.delete(record)
        db.commit()
        return {
            "message": "Transaction deleted successfully.",
            "deleted_id": transaction_id,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@app.get("/corrections")
def get_corrections(limit: int = 50, db: Session = Depends(get_db)):
    try:
        corrections = (
            db.query(TransactionCorrectionModel)
            .order_by(TransactionCorrectionModel.created_at.desc())
            .limit(limit)
            .all()
        )

        serialized = [
            {
                "id": c.id,
                "transaction_id": c.transaction_id,
                "original_description": c.original_description,
                "predicted_category": c.predicted_category,
                "corrected_category": c.corrected_category,
                "notes": c.notes,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in corrections
        ]

        return {"count": len(serialized), "corrections": serialized}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Correction history error: {str(e)}")


@app.post("/transactions/{transaction_id}/correction")
def teach_ai(
    transaction_id: int,
    item: TransactionCorrectionInput,
    db: Session = Depends(get_db),
):
    record = db.query(TransactionModel).filter(TransactionModel.id == transaction_id).first()

    if not record:
        raise HTTPException(status_code=404, detail="Transaction not found")

    corrected_category = item.corrected_category.strip()
    if not corrected_category:
        raise HTTPException(status_code=400, detail="Corrected category cannot be empty.")

    try:
        correction = TransactionCorrectionModel(
            transaction_id=record.id,
            original_description=record.description,
            predicted_category=record.category,
            corrected_category=corrected_category,
            notes=item.notes.strip() if item.notes else None,
        )

        record.category = corrected_category
        record.is_anomaly = check_for_anomaly(
            db,
            corrected_category,
            record.amount,
            exclude_id=record.id,
        )

        db.add(correction)
        db.commit()
        db.refresh(record)
        db.refresh(correction)

        return {
            "message": "Correction saved successfully.",
            "transaction": {
                "id": record.id,
                "date": record.date,
                "description": record.description,
                "category": record.category,
                "amount": record.amount,
                "is_anomaly": record.is_anomaly,
            },
            "correction": {
                "id": correction.id,
                "transaction_id": correction.transaction_id,
                "original_description": correction.original_description,
                "predicted_category": correction.predicted_category,
                "corrected_category": correction.corrected_category,
                "notes": correction.notes,
                "created_at": correction.created_at.isoformat() if correction.created_at else None,
            },
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Teach-AI save failed: {str(e)}")


@app.get("/analytics/summary")
def get_analytics_summary(
    search: Optional[str] = None,
    category: Optional[str] = None,
    only_anomalies: bool = False,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
):
    try:
        base_query = build_transaction_query(
            db=db,
            search=search,
            category=category,
            only_anomalies=only_anomalies,
            start_date=start_date,
            end_date=end_date,
        )

        total_spent = base_query.with_entities(func.sum(TransactionModel.amount)).scalar() or 0.0
        total_count = base_query.with_entities(func.count(TransactionModel.id)).scalar() or 0

        category_data = base_query.with_entities(
            TransactionModel.category,
            func.sum(TransactionModel.amount).label("total_amount"),
            func.count(TransactionModel.id).label("count"),
        ).group_by(TransactionModel.category).all()

        breakdown = [
            {
                "category": row.category,
                "total_amount": row.total_amount,
                "transaction_count": row.count,
                "percentage": round((row.total_amount / total_spent) * 100, 2) if total_spent > 0 else 0,
            }
            for row in category_data
        ]

        return {
            "overall": {
                "total_spent": round(total_spent, 2),
                "transaction_count": total_count,
            },
            "categorical_breakdown": breakdown,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics Engine Error: {str(e)}")