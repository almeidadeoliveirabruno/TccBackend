from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from models.appointment import AppointmentStatus
from typing import Union
from datetime import date

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

class RevenueByDay(BaseModel):
    date: date
    total_revenue: Decimal

RevenuePeriodResult = Union[RevenueByMonth, RevenueByDay]


class ExpenseByMonth(BaseModel):
    year: int
    month: int
    total_expense: Decimal
    model_config = ConfigDict(from_attributes=True)

class ExpenseByDay(BaseModel):
    date: date
    total_expense: Decimal

ExpensePeriodResult = Union[ExpenseByMonth, ExpenseByDay]

class AppointmentCount(BaseModel):
    status: AppointmentStatus
    count: int
    percentage: float

    model_config = ConfigDict(from_attributes=True)

class AppointmentByMonth(BaseModel):
    year: int
    month: int
    count: int

class AppointmentByDay(BaseModel):
    date: date
    count: int

AppointmentPeriodResult = Union[AppointmentByMonth, AppointmentByDay]

#Cards
class Profit(BaseModel):
    total_revenue: Decimal
    total_expense: Decimal
    profit: Decimal

class AttendancePercentage(BaseModel):
    attendance_percentage: float
    total: int