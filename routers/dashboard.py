from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db.dependencies import get_current_clinic_id, get_db
from schemas.dashboard import (
    DentistBillingSummary, 
    DentistCountSummary, 
    ProcedureBillingSummary,
    ProcedureCountSummary,
    RevenueByMonth,
    ExpenseByMonth,
    AppointmentCount,
    AttendanceByMonth,
    Profit,
    AttendancePercentage
                               )

from services.dashboard_service import ( 
    dentists_billing, 
    dentists_appointments_count, 
    procedures_billing,
    procedures_appointments_count,
    expense_by_month_billing,
    revenue_by_month_billing,
    appointments_count,
    attendance_by_month,
    profit,
    attendance_percentage
    )

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

#gráfico de barra lateral
@router.get("/dentist-billing-summary", response_model=list[DentistBillingSummary])
def dentist_billing_summary_route(
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
):
    return dentists_billing(db, clinic_id, start_date, end_date)

#Gráfico de barra lateral
@router.get("/dentist-appointments-count", response_model=list[DentistCountSummary])
def dentist_appointments_count_route(
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
):
    return dentists_appointments_count(db, clinic_id, start_date, end_date)

#Gráfico de barra lateral
@router.get("/procedure-billing-summary", response_model=list[ProcedureBillingSummary])
def procedures_billing_summary_route(
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
):
    return procedures_billing(db, clinic_id, start_date, end_date)

#Gráfico de barra lateral
@router.get("/procedure-appointments-count", response_model=list[ProcedureCountSummary])
def procedures_appointments_count_route(
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
):
    return procedures_appointments_count(db, clinic_id, start_date, end_date)

#gráfico de linha/área
@router.get("/revenue-summary", response_model=list[RevenueByMonth])
def revenue_summary_route(
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
):
    return revenue_by_month_billing(db, clinic_id, start_date, end_date)

#gráfico de linha/área
@router.get("/expense-summary", response_model=list[ExpenseByMonth])
def expense_summary_route(
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
):
    return expense_by_month_billing(db, clinic_id, start_date, end_date)

#gráfico de pizza
@router.get("/appointments-count", response_model=list[AppointmentCount])
def appointments_count_route(
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
):
    return appointments_count(db, clinic_id, start_date, end_date)

#gráfico de linha
@router.get("/attendance-summary", response_model=list[AttendanceByMonth])
def attendance_summary_route(
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
):
    return attendance_by_month(db, clinic_id, start_date, end_date)

#card 1,2 e 3
@router.get("/profit-cards", response_model=Profit)
def profit_cards_route(
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
):
    return profit(db, clinic_id, start_date, end_date)

#card 4
@router.get("/attendance-percentage", response_model=AttendancePercentage)
def attendance_percentage_route(
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
):
    return attendance_percentage(db, clinic_id, start_date, end_date)