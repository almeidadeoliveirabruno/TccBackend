from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.database import get_db
from schemas import dentist_schedule as schemas
from services import dentist_schedule_service as service
from auth import get_current_clinic_id  # ajuste pro caminho real da sua dependency

router = APIRouter(prefix="/dentists", tags=["dentist_schedule"])


@router.post("/{dentist_id}/schedules",response_model=schemas.AvailabilityResponse,status_code=201)
def create_schedules(
    dentist_id: int,
    payload: schemas.AvailabilityCreate,
    db: Session = Depends(get_db),
    current_clinic_id=Depends(get_current_clinic_id),
):
    return service.create_dentist_schedules(
        db=db,
        dentist_id=dentist_id,
        clinic_id=current_clinic_id,
        availability=payload.availability,
    )


@router.get("/{dentist_id}/schedules",response_model=list[schemas.ScheduleCreatedResponse],)
def list_schedules(
    dentist_id: int,
    db: Session = Depends(get_db),
    current_clinic_id=Depends(get_current_clinic_id),
):
    return service.list_dentist_schedules(
        db=db,
        dentist_id=dentist_id,
        clinic_id=current_clinic_id,
    )


@router.put(
    "/{dentist_id}/schedules/{dentist_schedule_id}",
    response_model=schemas.ScheduleCreatedResponse,
)
def update_schedule(
    dentist_id: int,
    dentist_schedule_id: int,
    payload: schemas.ScheduleUpdate,
    db: Session = Depends(get_db),
    current_clinic_id=Depends(get_current_clinic_id),
):
    return service.update_dentist_schedule(
        db=db,
        dentist_id=dentist_id,
        dentist_schedule_id=dentist_schedule_id,
        clinic_id=current_clinic_id,
        data=payload,
    )


@router.delete(
    "/{dentist_id}/schedules/{dentist_schedule_id}",
    status_code=204,
)
def delete_schedule(
    dentist_id: int,
    dentist_schedule_id: int,
    db: Session = Depends(get_db),
    current_clinic_id=Depends(get_current_clinic_id),
):
    service.delete_dentist_schedule(
        db=db,
        dentist_id=dentist_id,
        dentist_schedule_id=dentist_schedule_id,
        clinic_id=current_clinic_id,
    )