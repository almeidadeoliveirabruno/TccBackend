from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional
from enums.ReceivableStatus import ReceivableStatus
from pydantic import BaseModel, ConfigDict, Field

class ReceivableUpdate(BaseModel):
    status: Optional[ReceivableStatus] = None
    due_date: Optional[date] = None
    paid_at: Optional[datetime] = None
    payment_method: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = None


class ReceivableResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    appointment_id: int
    clinic_id: str
    total_amount: Decimal
    status: ReceivableStatus
    due_date: Optional[date] = None
    paid_at: Optional[datetime] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    is_paid: bool