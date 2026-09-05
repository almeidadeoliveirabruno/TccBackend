from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from db.dependencies import get_current_clinic_id, get_db
from schemas.home import (
    LastThreePatients,
    Finance,
    CardPatientsNumber,
    CardAppointmentToday,
    CardExpenseNotPaid,
    CardActiveDentist
)
from services.home_service import(
    last_five_patients,
    patients_count,
    appointments_today,
    expenses_not_paid,
    total_active_dentists
)
from services.dashboard_service import(
    profit
)

router = APIRouter(prefix="/home", tags=["Home"])

@router.get("/last-patients",response_model=list[LastThreePatients])
def last_patients_route(
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id)
):
    return last_five_patients(db, clinic_id)

@router.get('/finance', response_model= Finance)
def profit_route(
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id)
):
    return profit(db, clinic_id)

@router.get('/patients-count', response_model = CardPatientsNumber )
def patients_count_route(
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id)
):
    return patients_count(db, clinic_id)

@router.get('/appointments-today', response_model= CardAppointmentToday)
def appointments_today_route(
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id)
):
    return appointments_today(db, clinic_id)

@router.get('/expenses-not-paid', response_model= CardExpenseNotPaid )
def expenses_not_paid_route(
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id)
):
    return  expenses_not_paid(db, clinic_id)

@router.get('/dentist-count', response_model= CardActiveDentist )
def dentist_count_route(
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id)
):
    return total_active_dentists(db, clinic_id)