from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import TransactionCorrectionModel, TransactionModel
from api.schemas import TransactionCorrectionInput

router = APIRouter(prefix="/corrections", tags=["corrections"])

@router.get("/", response_model=dict)
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

@router.post("/transactions/{transaction_id}/correction", response_model=dict)
def teach_ai(transaction_id: int, item: TransactionCorrectionInput, db: Session = Depends(get_db)):
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
        db.add(correction)
        db.commit()
        db.refresh(record)
        db.refresh(correction)
        return {"message": "Correction saved successfully.", "transaction": {
            "id": record.id, "date": record.date, "description": record.description,
            "category": record.category, "amount": record.amount, "is_anomaly": record.is_anomaly
        }, "correction": {
            "id": correction.id, "transaction_id": correction.transaction_id,
            "original_description": correction.original_description,
            "predicted_category": correction.predicted_category,
            "corrected_category": correction.corrected_category,
            "notes": correction.notes, "created_at": correction.created_at.isoformat() if correction.created_at else None
        }}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Teach-AI save failed: {str(e)}")
