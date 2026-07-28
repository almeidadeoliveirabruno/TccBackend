from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db.dependencies import get_db, get_current_clinic_id
from schemas.common import PaginatedResponse
from schemas.dentist import (
    DentistCreate,
    DentistUpdate,
    DentistStatusUpdate,
    DentistResponse,
    DentistResponseDetail,
)
from models.dentist import DentistStatus
from services.dentist_service import (
    create_dentist,
    get_dentist_by_id,
    get_dentists_by_clinic_id,
    update_dentist,
    delete_dentist,
    update_dentist_status,
    get_distinct_specialties,
    get_dentist_detail
)
from services.dentist_schedule_service import create_dentist_schedules

router = APIRouter(prefix="/dentists", tags=["dentists"])


@router.post("", response_model=DentistResponseDetail, status_code=201)
def create_dentist_route(
    dentist_data: DentistCreate,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    dentist = create_dentist(db, dentist_data, clinic_id)

    if dentist_data.schedules:
        create_dentist_schedules(db, dentist.id, clinic_id, dentist_data.schedules)

    db.refresh(dentist)
    return dentist


@router.get("", response_model=PaginatedResponse[DentistResponse])
def list_dentists_route(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: str | None = None,
    specialty: str | None = None,
    status: DentistStatus | None = None,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    return get_dentists_by_clinic_id(
        db, clinic_id, page=page, page_size=page_size,
        search=search, specialty=specialty, status=status,
    )


@router.get("/specialties", response_model=list[str])
def list_specialties_route(
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    # PRECISA vir antes de "/{dentist_id}" neste arquivo: rotas com path
    # param casam por posição de registro, não por tipo — se
    # "/{dentist_id}" viesse primeiro, GET /dentists/specialties bateria
    # nela e o FastAPI tentaria converter "specialties" pra int (erro 422)
    # antes mesmo de considerar esta rota.
    return get_distinct_specialties(db, clinic_id)


@router.get("/{dentist_id}", response_model=DentistResponseDetail)
def get_dentist_route(
    dentist_id: int,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    return get_dentist_detail(db, dentist_id, clinic_id)


@router.put("/{dentist_id}", response_model=DentistResponseDetail)
def update_dentist_route(
    dentist_id: int,
    dentist_data: DentistUpdate,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    dentist = update_dentist(db, dentist_id, dentist_data, clinic_id)
    db.refresh(dentist)
    return dentist


@router.patch("/{dentist_id}/status", response_model=DentistResponseDetail)
def update_dentist_status_route(
    dentist_id: int,
    status_data: DentistStatusUpdate,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    dentist = update_dentist_status(db, dentist_id, status_data.status, clinic_id)
    db.refresh(dentist)
    return dentist


@router.delete("/{dentist_id}", status_code=204)
def delete_dentist_route(
    dentist_id: int,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    delete_dentist(db, dentist_id, clinic_id)