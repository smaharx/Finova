from sqlalchemy import Column, Integer, String, Float
from api.database import Base

class TransactionModel(Base):
    __tablename__ = "transactions"

    # Define the columns exactly mapping to your database schema
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date = Column(String, nullable=False)
    description = Column(String, nullable=False)
    category = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    is_anomaly = Column(Integer, default=0) # SQLite uses Int for Boolean typically