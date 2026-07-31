from sqlalchemy import (
    Boolean,
    Column,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from db.database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)

    clinic_id = Column(
        String(36),
        ForeignKey("clinics.id"),
        nullable=False,
        index=True,
    )

    description = Column(
        String,
        nullable=False,
    )

    category_id = Column(
        Integer,
        ForeignKey("expense_categories.id"),
        nullable=False,
    )

    amount = Column(
        Numeric(10, 2),
        nullable=False,
    )

    due_date = Column(
        Date,
        nullable=False,
    )

    payment_date = Column(
        Date,
        nullable=True,
    )

    paid = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    notes = Column(
        String,
        nullable=True,
    )

    clinic = relationship(
        "Clinic",
        back_populates="expenses",
    )

    category = relationship(
        "ExpenseCategory",
        back_populates="expenses",
    )