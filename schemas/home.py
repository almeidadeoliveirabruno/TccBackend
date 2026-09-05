from pydantic import BaseModel, ConfigDict
from datetime import datetime
from decimal import Decimal

class LastThreePatients(BaseModel):
    name: str
    phone: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
    
class Finance(BaseModel):
    total_revenue: Decimal
    total_expense: Decimal
    profit: Decimal
    model_config = ConfigDict(from_attributes=True)

class CardPatientsNumber(BaseModel):
    patients_count: int
    model_config = ConfigDict(from_attributes=True)

class CardAppointmentToday(BaseModel):
    appointments_count: int
    model_config = ConfigDict(from_attributes=True)

class CardExpenseNotPaid(BaseModel):
    expense_count: int
    model_config = ConfigDict(from_attributes=True)

class CardActiveDentist(BaseModel):
    dentist_count: int
    model_config = ConfigDict(from_attributes=True)
