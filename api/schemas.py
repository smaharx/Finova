from typing import Optional
from pydantic import BaseModel

class TransactionCreateInput(BaseModel):
    date: str
    description: str
    amount: float

class TransactionUpdateInput(BaseModel):
    date: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[str] = None

class TransactionOut(BaseModel):
    id: int
    date: str
    description: str
    category: str
    amount: float
    is_anomaly: int

class TransactionCreateResponse(BaseModel):
    message: str
    data: TransactionOut

class TransactionCorrectionInput(BaseModel):
    corrected_category: str
    notes: Optional[str] = None

class CorrectionOut(BaseModel):
    id: int
    transaction_id: int
    original_description: str
    predicted_category: str
    corrected_category: str
    notes: Optional[str]
    created_at: Optional[str]
