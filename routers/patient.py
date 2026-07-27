from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db.dependencies import get_db, get_current_clinic_id
from schemas.common import PaginatedResponse
from schemas.patient import (
    PatientCreate,
    PatientUpdate,
    PatientResponseCard,
    PatientResponseDetail,
)

from services.patient_service import (
    create_patient,
    update_patient,
    delete_patient,
    get_patient_by_id,
    get_patients_by_clinic_id,
    get_patient_detail
)

router = APIRouter(prefix="/patients", tags=["patients"])

@router.post("", response_model=PatientResponseDetail, status_code=201)
def create_patient_route(
    patient_data: PatientCreate,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    return create_patient(db, patient_data, clinic_id)

@router.get("", response_model=PaginatedResponse[PatientResponseCard])
def list_patients_route(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    search: str | None = None,
    clinic_id: str = Depends(get_current_clinic_id),
):
    return get_patients_by_clinic_id(
        db, clinic_id, page=page, page_size=page_size, search=search
    )

@router.get("/{patient_id}", response_model=PatientResponseDetail)
def get_patient_route(
    patient_id: int,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    return get_patient_detail(db, patient_id, clinic_id)


@router.put("/{patient_id}", response_model=PatientResponseDetail)
def update_patient_route(
    patient_id: int,
    patient_data: PatientUpdate,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    return update_patient(db, patient_id, patient_data, clinic_id)


@router.delete("/{patient_id}", status_code=204)
def delete_patient_route(
    patient_id: int,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    delete_patient(db, patient_id, clinic_id)