from datetime import datetime
import enum 

from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    DateTime,
    Text,
    CheckConstraint
)
from sqlalchemy.orm import relationship

from db.database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    clinic_id = Column(String(36), ForeignKey("clinics.id"), nullable=False, index=True)
    description = Column(String(255), nullable=False)  # Campo para falar o que é a despesa
    category = Column(String(50), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    due_date = Column(Date, nullable=False)
    paid_at = Column(DateTime, nullable=True)
    status = Column(String(10), nullable=False, default="pendente")
    notes = Column(Text, nullable=True)  # Campo para detalhar se necessário.
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    clinic = relationship("Clinic")
 
    __table_args__ = (
        CheckConstraint(
            "status IN ('pendente','pago','cancelado')", name="ck_expense_status"
        ),
    )