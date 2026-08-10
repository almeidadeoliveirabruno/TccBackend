from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from models.receivable import Receivable
from models.appointment import Appointment
from schemas.common import PaginatedResponse
from schemas.receivable import ReceivableUpdate
from enums.ReceivableStatus import ReceivableStatus


def create_receivable_for_appointment(
    db: Session,
    appointment: Appointment,
    clinic_id: str,
) -> Receivable:

    total_amount = sum(
        (item.unit_price for item in appointment.procedure_items),
        Decimal("0"),
    )

    receivable = Receivable(
        appointment_id=appointment.id,
        clinic_id=clinic_id,
        total_amount=total_amount,
        status=ReceivableStatus.PENDENTE.value,
    )
    db.add(receivable)
    db.flush()
    db.refresh(receivable)
    return receivable


def get_receivable(db: Session, clinic_id: str, receivable_id: int) -> Receivable:
    receivable = (
        db.query(Receivable)
        .filter(Receivable.id == receivable_id, Receivable.clinic_id == clinic_id)
        .first()
    )
    if receivable is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conta a receber não encontrada"
        )
    return receivable


def get_receivable_by_appointment_id(
    db: Session, clinic_id: str, appointment_id: int
) -> Receivable:
    receivable = (
        db.query(Receivable)
        .filter(
            Receivable.appointment_id == appointment_id,
            Receivable.clinic_id == clinic_id,
        )
        .first()
    )
    if receivable is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conta a receber não encontrada para essa consulta",
        )
    return receivable


def get_receivable_statistics(db: Session, clinic_id: str) -> dict:
    """
    Estatísticas fixas pros cards da página de Financeiro -- sempre
    sobre o total da clínica, independente dos filtros da listagem.
    """
    rows = (
        db.query(Receivable.status, func.sum(Receivable.total_amount), func.count(Receivable.id))
        .filter(Receivable.clinic_id == clinic_id)
        .group_by(Receivable.status)
        .all()
    )
    stats = {
        "total_pendente": Decimal("0"), "count_pendente": 0,
        "total_parcial": Decimal("0"), "count_parcial": 0,
        "total_pago": Decimal("0"), "count_pago": 0,
        "total_cancelado": Decimal("0"), "count_cancelado": 0,
    }
    for status_value, amount_sum, count in rows:
        stats[f"total_{status_value}"] = amount_sum or Decimal("0")
        stats[f"count_{status_value}"] = count
    return stats


def list_receivables(
    db: Session,
    clinic_id: str,
    *,
    receivable_status: Optional[ReceivableStatus] = None,
    due_date_from: Optional[date] = None,
    due_date_to: Optional[date] = None,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedResponse:
    query = db.query(Receivable).filter(Receivable.clinic_id == clinic_id)

    if receivable_status is not None:
        query = query.filter(Receivable.status == receivable_status.value)
    if due_date_from is not None:
        query = query.filter(Receivable.due_date >= due_date_from)
    if due_date_to is not None:
        query = query.filter(Receivable.due_date <= due_date_to)

    total = query.count()
    items = (
        query.order_by(Receivable.due_date.asc())
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
        statistics={"receivable_statistics": get_receivable_statistics(db, clinic_id)},
    )


def update_receivable(
    db: Session, clinic_id: str, receivable_id: int, data: ReceivableUpdate
) -> Receivable:
    """
    Edição geral (due_date, notes, payment_method, status manual).
    Não é o caminho recomendado pra marcar como pago -- ver
    mark_receivable_as_paid, que garante status + paid_at juntos.
    """
    receivable = get_receivable(db, clinic_id, receivable_id)

    if receivable.status == ReceivableStatus.CANCELADO.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível editar uma conta a receber cancelada",
        )

    update_data = data.model_dump(exclude_unset=True)

    if "status" in update_data and update_data["status"] is not None:
        update_data["status"] = data.status.value

    for field, value in update_data.items():
        setattr(receivable, field, value)

    db.flush()
    db.refresh(receivable)
    return receivable


def mark_receivable_as_paid(
    db: Session,
    clinic_id: str,
    receivable_id: int,
    payment_method: Optional[str] = None,
    paid_at: Optional[datetime] = None,
) -> Receivable:
    receivable = get_receivable(db, clinic_id, receivable_id)

    if receivable.status == ReceivableStatus.CANCELADO.value:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Não é possível marcar como paga uma conta cancelada")
    if receivable.status == ReceivableStatus.PAGO.value:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Conta já está paga")

    paid_at = paid_at or datetime.utcnow()
    if paid_at > datetime.utcnow():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Data de pagamento não pode ser no futuro")

    receivable.status = ReceivableStatus.PAGO.value
    receivable.paid_at = paid_at
    if payment_method is not None:
        receivable.payment_method = payment_method

    db.flush()
    db.refresh(receivable)
    return receivable


def cancel_receivable(db: Session, clinic_id: str, receivable_id: int) -> Receivable:
    receivable = get_receivable(db, clinic_id, receivable_id)

    if receivable.status == ReceivableStatus.PAGO.value:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Não é possível cancelar uma conta já paga")

    receivable.status = ReceivableStatus.CANCELADO.value

    db.flush()
    db.refresh(receivable)
    return receivable