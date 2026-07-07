from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from sqlalchemy import func
from api.database import get_db
from api.models import TransactionModel

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/summary", response_model=dict)
def get_analytics_summary(
    search: Optional[str] = None,
    category: Optional[str] = None,
    only_anomalies: bool = False,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db = Depends(get_db),
):
    try:
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

        total_spent = query.with_entities(func.sum(TransactionModel.amount)).scalar() or 0.0
        total_count = query.with_entities(func.count(TransactionModel.id)).scalar() or 0
        category_data = (
            query.with_entities(
                TransactionModel.category,
                func.sum(TransactionModel.amount).label("total_amount"),
                func.count(TransactionModel.id).label("count"),
            )
            .group_by(TransactionModel.category)
            .all()
        )
        breakdown = [
            {
                "category": row.category,
                "total_amount": row.total_amount,
                "transaction_count": row.count,
                "percentage": round((row.total_amount / total_spent) * 100, 2) if total_spent > 0 else 0,
            }
            for row in category_data
        ]
        return {"overall": {"total_spent": round(total_spent, 2), "transaction_count": total_count}, "categorical_breakdown": breakdown}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics Engine Error: {str(e)}")
