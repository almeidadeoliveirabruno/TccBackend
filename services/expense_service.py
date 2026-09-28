from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from models.expense import Expense
from schemas.common import PaginatedResponse
from schemas.expense import ExpenseCreate, ExpenseUpdate
from enums.ExpenseStatus import ExpenseStatus
from enums.ExpenseCategory import ExpenseCategory


def create_expense(db: Session, clinic_id: str, data: ExpenseCreate) -> Expense:
    status_value = data.status.value if data.status is not None else ExpenseStatus.PENDENTE.value
    paid_at = data.paid_at if status_value == ExpenseStatus.PAGO.value else None
    if status_value == ExpenseStatus.PAGO.value and paid_at is None:
        paid_at = date.today()

    expense = Expense(
        clinic_id=clinic_id,
        description=data.description,
        category=data.category.value,
        amount=data.amount,
        due_date=data.due_date,
        paid_at=paid_at,
        notes=data.notes,
        status=status_value,
    )
    db.add(expense)
    db.flush()
    db.refresh(expense)
    return expense


def get_expense(db: Session, clinic_id: str, expense_id: int) -> Expense:
    expense = (
        db.query(Expense)
        .filter(Expense.id == expense_id, Expense.clinic_id == clinic_id)
        .first()
    )
    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Despesa não encontrada"
        )
    return expense


def get_expense_statistics(db: Session, clinic_id: str) -> dict:
    """
    Estatísticas fixas pros cards da página de Despesas — sempre sobre
    o total da clínica, independente dos filtros aplicados na listagem.
    """
    rows = (
        db.query(Expense.status, func.sum(Expense.amount), func.count(Expense.id))
        .filter(Expense.clinic_id == clinic_id)
        .group_by(Expense.status)
        .all()
    )
    stats = {
        "total_pendente": Decimal("0"), "count_pendente": 0,
        "total_pago": Decimal("0"), "count_pago": 0,
        "total_geral": Decimal("0"), "count_geral": 0,
    }
    for row in rows:
        status_value = row[0]
        amount_sum = row[1] or Decimal("0")
        count = row[2] or 0
        if status_value == ExpenseStatus.PENDENTE.value:
            stats["total_pendente"] = amount_sum
            stats["count_pendente"] = count
        elif status_value == ExpenseStatus.PAGO.value:
            stats["total_pago"] = amount_sum
            stats["count_pago"] = count
        stats["total_geral"] += amount_sum
        stats["count_geral"] += count

    return stats


def list_expenses(
    db: Session,
    clinic_id: str,
    *,
    expense_status: Optional[ExpenseStatus] = None,
    category: Optional[ExpenseCategory] = None,
    due_date_from: Optional[date] = None,
    due_date_to: Optional[date] = None,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedResponse:
    query = db.query(Expense).filter(Expense.clinic_id == clinic_id)

    if expense_status is not None:
        query = query.filter(Expense.status == expense_status.value)
    if category is not None:
        query = query.filter(Expense.category == category.value)
    if due_date_from is not None:
        query = query.filter(Expense.due_date >= due_date_from)
    if due_date_to is not None:
        query = query.filter(Expense.due_date <= due_date_to)

    total = query.count()
    items = (
        query.order_by(Expense.due_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    total_pages = -(-total // page_size) if total else 0

    return PaginatedResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        statistics={"expense_statistics": get_expense_statistics(db, clinic_id)},
    )


def update_expense(db: Session, clinic_id: str, expense_id: int, data: ExpenseUpdate) -> Expense:
    expense = get_expense(db, clinic_id, expense_id)

    update_data = data.model_dump(exclude_unset=True)

    if "category" in update_data and update_data["category"] is not None:
        update_data["category"] = data.category.value
    if "status" in update_data and update_data["status"] is not None:
        update_data["status"] = data.status.value
        if data.status == ExpenseStatus.PAGO and not expense.paid_at and "paid_at" not in update_data:
            update_data["paid_at"] = date.today()
        elif data.status == ExpenseStatus.PENDENTE:
            update_data["paid_at"] = None

    for field, value in update_data.items():
        setattr(expense, field, value)

    db.flush()
    db.refresh(expense)
    return expense


def mark_expense_as_paid(
    db: Session, clinic_id: str, expense_id: int, paid_at: Optional[date] = None
) -> Expense:
    expense = get_expense(db, clinic_id, expense_id)

    paid_at = paid_at or date.today()
    if paid_at > date.today():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Data de pagamento não pode ser no futuro")

    expense.status = ExpenseStatus.PAGO.value
    expense.paid_at = paid_at

    db.flush()
    db.refresh(expense)
    return expense


def unmark_expense_as_paid(db: Session, clinic_id: str, expense_id: int) -> Expense:
    expense = get_expense(db, clinic_id, expense_id)

    expense.status = ExpenseStatus.PENDENTE.value
    expense.paid_at = None

    db.flush()
    db.refresh(expense)
    return expense


def delete_expense(db: Session, clinic_id: str, expense_id: int) -> None:
    expense = get_expense(db, clinic_id, expense_id)
    db.delete(expense)
    db.flush()