from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from api.database import get_db
from api.models import TransactionModel, TransactionCorrectionModel
from api.schemas import (
    TransactionCreateInput,
    TransactionCreateResponse,
    TransactionUpdateInput,
    TransactionOut,
    TransactionCorrectionInput,
)

from api.ml import predict_category

router = APIRouter(prefix="/transactions", tags=["transactions"])

def check_for_anomaly(db: Session, category: str, new_amount: float, exclude_id: Optional[int] = None):
    import statistics
    query = db.query(TransactionModel.amount).filter(TransactionModel.category == category)
    if exclude_id:
        query = query.filter(TransactionModel.id != exclude_id)
    history = query.order_by(TransactionModel.id.desc()).limit(20).all()
    if len(history) < 5:
        return 0
    amounts = [h[0] for h in history]
    mean = statistics.mean(amounts)
    std_dev = statistics.stdev(amounts)
    if std_dev == 0:
        return 0
    z_score = abs(new_amount - mean) / std_dev
    return 1 if z_score > 3 else 0

@router.get("/", response_model=dict)
def get_transactions(
    limit: int = 50,
    search: Optional[str] = None,
    category: Optional[str] = None,
    only_anomalies: bool = False,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
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
    transactions = query.order_by(TransactionModel.date.desc()).limit(limit).all()
    serialized = [
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
    return {"count": len(serialized), "transactions": serialized}

@router.post("/", response_model=TransactionCreateResponse)
def create_transaction(item: TransactionCreateInput, db: Session = Depends(get_db)):
    predicted_cat = predict_category(item.description)
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

@router.put("/{transaction_id}", response_model=dict)
def update_transaction(transaction_id: int, item: TransactionUpdateInput, db: Session = Depends(get_db)):
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
            record.category = predict_category(record.description)
        record.is_anomaly = check_for_anomaly(db, record.category, record.amount, exclude_id=record.id)
        db.commit()
        db.refresh(record)
        return {"message": "Transaction updated successfully.", "data": {
            "id": record.id, "date": record.date, "description": record.description,
            "category": record.category, "amount": record.amount, "is_anomaly": record.is_anomaly
        }}
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

@router.delete("/{transaction_id}", response_model=dict)
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    record = db.query(TransactionModel).filter(TransactionModel.id == transaction_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Transaction not found")
    try:
        db.delete(record)
        db.commit()
        return {"message": "Transaction deleted successfully.", "deleted_id": transaction_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

# Compatibility endpoint: keep the original path for corrections so existing clients/tests continue to work
@router.post("/{transaction_id}/correction", response_model=dict)
def teach_ai_transaction(transaction_id: int, item: TransactionCorrectionInput, db: Session = Depends(get_db)):
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
        record.is_anomaly = check_for_anomaly(db, corrected_category, record.amount, exclude_id=record.id)

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
