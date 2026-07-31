from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db.dependencies import get_current_clinic_id, get_db
from models.appointment import AppointmentStatus
from schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentResponseCard,
    AppointmentStatusUpdate,
    AppointmentUpdate,
    TableDataLinePaginatedResponse,
    TableDetail,
)
from services.appointment_service import (
    confirm_appointment,
    create_appointment,
    delete_appointment,
    get_appointment_by_id,
    get_appointments_by_clinic_id,
    get_available_times,
    mark_confirmation_message_sent,
    update_appointment,
    update_appointment_status,
    get_appointments_by_clinic_id_for_table,
    get_appointment_detail_by_id,
    update_appointment_detail
)

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.get("/available-times")
def get_available_times_route(
    dentist_id: int = Query(...),
    appointment_date: date = Query(...),
    duration_minutes: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    return get_available_times(
        db=db,
        dentist_id=dentist_id,
        appointment_date=appointment_date,
        duration_minutes=duration_minutes,
        clinic_id=clinic_id,
    )


@router.post("", response_model=AppointmentResponse, status_code=201)
def create_appointment_route(
    appointment: AppointmentCreate,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    return create_appointment(
        db,
        appointment,
        clinic_id,
    )


@router.get("", response_model=list[AppointmentResponseCard])
def list_appointments_route(
    dentist_id: int | None = None,
    patient_id: int | None = None,
    appointment_date: date | None = None,
    appointment_status: AppointmentStatus | None = None,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    return get_appointments_by_clinic_id(
        db=db,
        clinic_id=clinic_id,
        dentist_id=dentist_id,
        patient_id=patient_id,
        appointment_date=appointment_date,
        appointment_status=appointment_status,
    )


@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment_route(
    appointment_id: int,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    return get_appointment_by_id(
        db,
        appointment_id,
        clinic_id,
    )


@router.put("/{appointment_id}", response_model=AppointmentResponse)
def update_appointment_route(
    appointment_id: int,
    appointment: AppointmentUpdate,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    return update_appointment(
        db,
        appointment_id,
        appointment,
        clinic_id,
    )

@router.patch("/{appointment_id}/confirm", response_model=AppointmentResponse)
def confirm_appointment_route(
    appointment_id: int,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    return confirm_appointment(
        db,
        appointment_id,
        clinic_id,
    )

@router.patch("/{appointment_id}/confirmation-message", response_model=AppointmentResponse)
def mark_confirmation_message_sent_route(
    appointment_id: int,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    return mark_confirmation_message_sent(
        db,
        appointment_id,
        clinic_id,
    )

@router.patch("/{appointment_id}/status", response_model=AppointmentResponse)
def update_status_route(
    appointment_id: int,
    appointment_status: AppointmentStatusUpdate,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    return update_appointment_status(
        db,
        appointment_id,
        appointment_status.status,
        clinic_id,
    )

@router.delete("/{appointment_id}", status_code=204)
def delete_appointment_route(
    appointment_id: int,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    delete_appointment(
        db,
        appointment_id,
        clinic_id,
    )

@router.get("/appointments/table", response_model=TableDataLinePaginatedResponse)
def list_appointments_table(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    dentist: str | None = Query(None),
    patient: str | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    status: AppointmentStatus | None = Query(None),
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    return get_appointments_by_clinic_id_for_table(
        db=db,
        clinic_id=clinic_id,
        page=page,
        page_size=page_size,
        dentist=dentist,
        patient=patient,
        start_date=start_date,
        end_date=end_date,
        status=status,
    )

@router.get("/appointments/{appointment_id}", response_model=TableDetail)
def get_appointment_detail(
    appointment_id: int ,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    return get_appointment_detail_by_id(
        db=db,
        appointment_id=appointment_id,
        clinic_id=clinic_id,
    )


@router.put("/appointments/{appointment_id}", response_model=TableDetail)
def update_appointment(
    appointment_update: AppointmentUpdate,
    appointment_id: int ,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    return update_appointment_detail(
        db=db,
        appointment_id=appointment_id,
        appointment_update=appointment_update,
        clinic_id=clinic_id,
    )