# routers/expense.py

from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db.dependencies import get_db, get_current_clinic_id
from schemas.common import PaginatedResponse
from schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseResponse
from enums.ExpenseStatus import ExpenseStatus
from enums.ExpenseCategory import ExpenseCategory

from services.expense_service import (
    create_expense,
    get_expense,
    list_expenses,
    update_expense,
    mark_expense_as_paid,
    cancel_expense,
)

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.post("", response_model=ExpenseResponse, status_code=201)
def create_expense_route(
    expense_data: ExpenseCreate,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    return create_expense(db, clinic_id, expense_data)


@router.get("", response_model=PaginatedResponse[ExpenseResponse])
def list_expenses_route(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: ExpenseStatus | None = None,
    category: ExpenseCategory | None = None,
    due_date_from: date | None = None,
    due_date_to: date | None = None,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    return list_expenses(
        db,
        clinic_id,
        expense_status=status,
        category=category,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
        page=page,
        page_size=page_size,
    )


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense_route(
    expense_id: int,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    return get_expense(db, clinic_id, expense_id)


@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense_route(
    expense_id: int,
    expense_data: ExpenseUpdate,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    return update_expense(db, clinic_id, expense_id, expense_data)


@router.post("/{expense_id}/pay", response_model=ExpenseResponse)
def pay_expense_route(
    expense_id: int,
    paid_at: datetime | None = None,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    return mark_expense_as_paid(db, clinic_id, expense_id, paid_at)


@router.post("/{expense_id}/cancel", response_model=ExpenseResponse)
def cancel_expense_route(
    expense_id: int,
    db: Session = Depends(get_db),
    clinic_id: str = Depends(get_current_clinic_id),
):
    return cancel_expense(db, clinic_id, expense_id)


@router.get("/categories", response_model=list[str])
def list_expense_categories_route():
    """Categorias sugeridas pro frontend popular um <select>."""
    return [c.value for c in ExpenseCategory]