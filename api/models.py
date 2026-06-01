from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from api.database import Base


class TransactionModel(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date = Column(String, nullable=False)
    description = Column(String, nullable=False)
    category = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    is_anomaly = Column(Integer, default=0)

    corrections = relationship(
        "TransactionCorrectionModel",
        back_populates="transaction",
        cascade="all, delete-orphan",
    )


class TransactionCorrectionModel(Base):
    __tablename__ = "transaction_corrections"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_id = Column(
        Integer,
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_description = Column(String, nullable=False)
    predicted_category = Column(String, nullable=False)
    corrected_category = Column(String, nullable=False)
    notes = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    transaction = relationship("TransactionModel", back_populates="corrections")
