from pydantic import BaseModel, ConfigDict
from datetime import datetime
from decimal import Decimal
from models.appointment import AppointmentStatus
from datetime import date, time

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

class AppointmentSummary(BaseModel):
    patient_name: str
    procedure_name: list[str] = []
    appointment_date: date
    time_begin: time
    time_end: time
    appointment_status: AppointmentStatus

    model_config = ConfigDict(from_attributes=True)


class NextAppointmentsByDentist(BaseModel):
    dentist_name: str
    appointments: list[AppointmentSummary] = []

    model_config = ConfigDict(from_attributes=True)
    
class ProcedureCategoryDistribution(BaseModel):
    category_name: str
    percentage: float

    model_config = ConfigDict(from_attributes=True)