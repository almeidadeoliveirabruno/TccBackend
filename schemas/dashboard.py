from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from models.appointment import AppointmentStatus

class DentistBillingSummary(BaseModel):
    name: str
    total_billing: Decimal
    model_config = ConfigDict(from_attributes=True)

class DentistCountSummary(BaseModel):
    name: str
    appointments_count: int
    model_config = ConfigDict(from_attributes=True)

class ProcedureBillingSummary(BaseModel):
    name: str
    total_billing: Decimal
    model_config = ConfigDict(from_attributes=True)

class ProcedureCountSummary(BaseModel):
    name: str
    appointments_count: int
    model_config = ConfigDict(from_attributes=True)

class RevenueByMonth(BaseModel):
    year: int
    month: int
    total_revenue: Decimal
    model_config = ConfigDict(from_attributes=True)


class ExpenseByMonth(BaseModel):
    year: int
    month: int
    total_expense: Decimal
    model_config = ConfigDict(from_attributes=True)

class AppointmentCount(BaseModel):
    status: AppointmentStatus
    count: int
    percentage: float

    model_config = ConfigDict(from_attributes=True)

class AttendanceByMonth(BaseModel):
    year: int
    month: int
    realized: int
    absent: int
    attendance_percentage: float

#Cards
class Profit(BaseModel):
    total_revenue: Decimal
    total_expense: Decimal
    profit: Decimal

class AttendancePercentage(BaseModel):
    attendance_percentage: float
    total: int