from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db.dependencies import get_db, get_current_clinic_id
from schemas.common import PaginatedResponse
from schemas.receivable import ReceivableUpdate, ReceivableResponse
from enums.ReceivableStatus import ReceivableStatus

from services.receivable_service import (
    get_receivable,
    get_receivable_by_appointment_id,
    list_receivables,
    update_receivable,
    mark_receivable_as_paid,
    cancel_receivable,
)

router = APIRouter(prefix="/receivables", tags=["receivables"])


@router.get("", response_model=PaginatedResponse[ReceivableResponse])
def list_receivables_route(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: ReceivableStatus | None = None,
    due_date_from: date | None = None,
    due_date_to: date | None = None,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    return list_receivables(
        db,
        clinic_id,
        receivable_status=status,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
        page=page,
        page_size=page_size,
    )


@router.get("/by-appointment/{appointment_id}", response_model=ReceivableResponse)
def get_receivable_by_appointment_route(
    appointment_id: int,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    return get_receivable_by_appointment_id(db, clinic_id, appointment_id)


@router.get("/{receivable_id}", response_model=ReceivableResponse)
def get_receivable_route(
    receivable_id: int,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    return get_receivable(db, clinic_id, receivable_id)


@router.put("/{receivable_id}", response_model=ReceivableResponse)
def update_receivable_route(
    receivable_id: int,
    receivable_data: ReceivableUpdate,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    return update_receivable(db, clinic_id, receivable_id, receivable_data)


@router.post("/{receivable_id}/pay", response_model=ReceivableResponse)
def pay_receivable_route(
    receivable_id: int,
    payment_method: str | None = None,
    paid_at: datetime | None = None,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    return mark_receivable_as_paid(db, clinic_id, receivable_id, payment_method, paid_at)


@router.post("/{receivable_id}/cancel", response_model=ReceivableResponse)
def cancel_receivable_route(
    receivable_id: int,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    return cancel_receivable(db, clinic_id, receivable_id)