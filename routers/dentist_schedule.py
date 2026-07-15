from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.dependencies import get_db, get_current_clinic_id
from schemas.dentist_schedule import (
    AvailabilityCreate,
    AvailabilityResponse,
    ScheduleUpdate,
    ScheduleCreatedResponse,
)
from services.dentist_schedule_service import (
    create_dentist_schedules,
    list_dentist_schedules,
    update_dentist_schedule,
    delete_dentist_schedule,
)

router = APIRouter(prefix="/dentists/{dentist_id}/schedules", tags=["dentist-schedules"])


@router.post("", response_model=AvailabilityResponse, status_code=201)
def create_schedules_route(
    dentist_id: int,
    data: AvailabilityCreate,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    return create_dentist_schedules(db, dentist_id, clinic_id, data.availability)


@router.get("", response_model=list[ScheduleCreatedResponse])
def list_schedules_route(
    dentist_id: int,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    return list_dentist_schedules(db, dentist_id, clinic_id)


@router.put("/{dentist_schedule_id}", response_model=ScheduleCreatedResponse)
def update_schedule_route(
    dentist_id: int,
    dentist_schedule_id: int,
    data: ScheduleUpdate,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    return update_dentist_schedule(db, dentist_id, dentist_schedule_id, clinic_id, data)


@router.delete("/{dentist_schedule_id}", status_code=204)
def delete_schedule_route(
    dentist_id: int,
    dentist_schedule_id: int,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    delete_dentist_schedule(db, dentist_id, dentist_schedule_id, clinic_id)