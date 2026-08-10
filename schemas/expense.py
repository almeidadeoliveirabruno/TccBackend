# schemas/finance_schemas.py — trecho de Expense

from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from enums.ExpenseStatus import ExpenseStatus
from enums.ExpenseCategory import ExpenseCategory


class ExpenseCreate(BaseModel):
    description: str = Field(..., max_length=255)
    category: ExpenseCategory
    amount: Decimal = Field(..., gt=0)
    due_date: date
    notes: Optional[str] = None

    @field_validator("description")
    @classmethod
    def description_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Descrição não pode ser vazia")
        return v


class ExpenseUpdate(BaseModel):
    description: Optional[str] = Field(None, max_length=255)
    category: Optional[ExpenseCategory] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    due_date: Optional[date] = None
    paid_at: Optional[datetime] = None
    status: Optional[ExpenseStatus] = None
    notes: Optional[str] = None

    @field_validator("description")
    @classmethod
    def description_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Descrição não pode ser vazia")
        return v

    @field_validator("paid_at")
    @classmethod
    def paid_at_not_in_future(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None and v > datetime.utcnow():
            raise ValueError("Data de pagamento não pode ser no futuro")
        return v


class ExpenseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    clinic_id: str
    description: str
    category: ExpenseCategory
    amount: Decimal
    due_date: date
    paid_at: Optional[datetime] = None
    status: ExpenseStatus
    notes: Optional[str] = None
    created_at: datetime