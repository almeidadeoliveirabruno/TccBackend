from datetime import date
from typing import Optional
from models import *
from enums.ReceivableStatus import ReceivableStatus
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case
from models.appointment import AppointmentStatus
from models.associations.appointment_procedure import AppointmentProcedure

# Controle Dentistas
#gráfico de barras lateral
def dentists_billing(
    db: Session,
    clinic_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    receivable_conditions = [Receivable.status == ReceivableStatus.PAGO.value]
    if start_date:
        receivable_conditions.append(Receivable.paid_at >= start_date)
    if end_date:
        receivable_conditions.append(Receivable.paid_at <= end_date)

    results = (
        db.query(
            Dentist.name,
            func.coalesce(func.sum(Receivable.total_amount), 0).label("total_billing")
        )
        .filter(Dentist.clinic_id == clinic_id)
        .outerjoin(Appointment, Appointment.dentist_id == Dentist.id)
        .outerjoin(
            Receivable,
            and_(
                Receivable.appointment_id == Appointment.id,
                *receivable_conditions
            )
        )
        .group_by(Dentist.name)
        .order_by(func.coalesce(func.sum(Receivable.total_amount), 0).desc())
        .all()
    )
    return results

#gráfico de barras lateral
def dentists_appointments_count(
    db: Session,
    clinic_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    appointment_conditions = [
        Appointment.clinic_id == clinic_id,
        Appointment.status == AppointmentStatus.REALIZADO.value,
    ]
    if start_date:
        appointment_conditions.append(Appointment.appointment_date >= start_date)
    if end_date:
        appointment_conditions.append(Appointment.appointment_date <= end_date)

    results = (
        db.query(
            Dentist.name,
            func.count(Appointment.id).label("appointments_count")
        )
        .filter(Dentist.clinic_id == clinic_id)
        .outerjoin(
            Appointment,
            and_(
                Appointment.dentist_id == Dentist.id,
                *appointment_conditions
            )
        )
        .group_by(Dentist.name)
        .order_by(func.count(Appointment.id).desc())
        .all()
    )
    return results


# Controle Procedimentos
#gráfico de barras lateral
def procedures_billing(
    db: Session,
    clinic_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    appointment_conditions = [Appointment.clinic_id == clinic_id]
    receivable_conditions = [Receivable.status == ReceivableStatus.PAGO.value]
    if start_date:
        receivable_conditions.append(Receivable.paid_at >= start_date)
    if end_date:
        receivable_conditions.append(Receivable.paid_at <= end_date)

    results = (
        db.query(
            Procedure.name,
            func.coalesce(func.sum(Receivable.total_amount), 0).label("total_billing")
        )
        .filter(Procedure.clinic_id == clinic_id)
        .outerjoin(
            AppointmentProcedure,
            AppointmentProcedure.procedure_id == Procedure.id
        )
        .outerjoin(
            Appointment,
            and_(
                Appointment.id == AppointmentProcedure.appointment_id,
                *appointment_conditions
            )
        )
        .outerjoin(
            Receivable,
            and_(
                Receivable.appointment_id == Appointment.id,
                *receivable_conditions
            )
        )
        .group_by(Procedure.name)
        .order_by(func.coalesce(func.sum(Receivable.total_amount), 0).desc())
        .all()
    )
    return results

#gráfico de barras lateral
def procedures_appointments_count(
    db: Session,
    clinic_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    appointment_conditions = [Appointment.clinic_id == clinic_id,
                              Appointment.status == AppointmentStatus.REALIZADO.value,]
    if start_date:
        appointment_conditions.append(Appointment.appointment_date >= start_date)
    if end_date:
        appointment_conditions.append(Appointment.appointment_date <= end_date)

    results = (
        db.query(
            Procedure.name,
            func.count(Appointment.id).label("appointments_count")
        )
        .filter(Procedure.clinic_id == clinic_id)
        .outerjoin(AppointmentProcedure,
                    AppointmentProcedure.procedure_id == Procedure.id)
        .outerjoin(
            Appointment,
            and_(
                Appointment.id == AppointmentProcedure.appointment_id,
                *appointment_conditions
            )
        )
        .group_by(Procedure.id, Procedure.name)
        .order_by(func.count(Appointment.id).desc())
        .all()
    )
    return results

#gráfico de linhas/área que vai juntar com despesa
def revenue_by_month_billing(
    db: Session,
    clinic_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    filters = [
        Receivable.clinic_id == clinic_id,
        Receivable.status == ReceivableStatus.PAGO.value,
    ]

    if start_date:
        filters.append(Receivable.paid_at >= start_date)

    if end_date:
        filters.append(Receivable.paid_at <= end_date)

    return (
        db.query(
            func.year(Receivable.paid_at).label("year"),
            func.month(Receivable.paid_at).label("month"),
            func.sum(Receivable.total_amount).label("total_revenue")
        )
        .filter(*filters)
        .group_by(
            func.year(Receivable.paid_at),
            func.month(Receivable.paid_at)
        )
        .order_by(
            func.year(Receivable.paid_at),
            func.month(Receivable.paid_at)
        )
        .all()
    )

#gráfico de linhas/área que vai juntar com receita
def expense_by_month_billing(
    db: Session,
    clinic_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    filters = [
        Expense.clinic_id == clinic_id
    ]

    if start_date:
        filters.append(Expense.due_date >= start_date)

    if end_date:
        filters.append(Expense.due_date <= end_date)

    return (
        db.query(
            func.year(Expense.due_date).label("year"),
            func.month(Expense.due_date).label("month"),
            func.sum(Expense.amount).label("total_expense")
        )
        .filter(*filters)
        .group_by(
            func.year(Expense.due_date),
            func.month(Expense.due_date)
        )
        .order_by(
            func.year(Expense.due_date),
            func.month(Expense.due_date)
        )
        .all()
    )

#Controle appointments

def appointments_count(
    db: Session,
    clinic_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    filters = [Appointment.clinic_id == clinic_id]
    if start_date:
        filters.append(Appointment.appointment_date >= start_date)
    if end_date:
        filters.append(Appointment.appointment_date <= end_date)

    results = (
        db.query(
            Appointment.status.label("appointments_status"),
            func.count(Appointment.id).label("count")
        )
        .filter(*filters)
        .group_by(Appointment.status)
        .all()
    )

    total = sum(row.count for row in results)

    return [
        {
            "status": row.appointments_status,
            "count": row.count,
            "percentage": round((row.count / total) * 100, 2) if total > 0 else 0,
        }
        for row in results
    ]

#Gráfico de linha
def attendance_by_month(
    db: Session,
    clinic_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    filters = [
        Appointment.clinic_id == clinic_id,
        Appointment.status.in_([
            AppointmentStatus.REALIZADO.value,
            AppointmentStatus.FALTOU.value,
        ])
    ]

    if start_date:
        filters.append(Appointment.appointment_date >= start_date)

    if end_date:
        filters.append(Appointment.appointment_date <= end_date)

    realized = func.sum(
        case(
            (Appointment.status == AppointmentStatus.REALIZADO.value, 1),
            else_=0
        )
    )

    total = func.count(Appointment.id)

    results = (
        db.query(
            func.year(Appointment.appointment_date).label("year"),
            func.month(Appointment.appointment_date).label("month"),
            realized.label("realized"),
            func.sum(
                case(
                    (Appointment.status == AppointmentStatus.FALTOU.value, 1),
                    else_=0
                )
            ).label("absent"),
            (
                realized * 100.0 / func.nullif(total, 0)
            ).label("attendance_percentage")
        )
        .filter(*filters)
        .group_by(
            func.year(Appointment.appointment_date),
            func.month(Appointment.appointment_date)
        )
        .order_by(
            func.year(Appointment.appointment_date),
            func.month(Appointment.appointment_date)
        )
        .all()
    )

    return results

def expense_per_category(
    db: Session,
    clinic_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    ...

#cards
def profit(
    db: Session,
    clinic_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    revenue_filters = [
        Receivable.clinic_id == clinic_id,
        Receivable.status == ReceivableStatus.PAGO.value,
    ]

    expense_filters = [
        Expense.clinic_id == clinic_id
    ]

    if start_date:
        revenue_filters.append(Receivable.paid_at >= start_date)
        expense_filters.append(Expense.due_date >= start_date)

    if end_date:
        revenue_filters.append(Receivable.paid_at <= end_date)
        expense_filters.append(Expense.due_date <= end_date)

    revenue = (
        db.query(
            func.coalesce(
                func.sum(Receivable.total_amount),
                0
            )
        )
        .filter(*revenue_filters)
        .scalar()
    )

    expense = (
        db.query(
            func.coalesce(
                func.sum(Expense.amount),
                0
            )
        )
        .filter(*expense_filters)
        .scalar()
    )

    return {
        "total_revenue": revenue,
        "total_expense": expense,
        "profit": revenue - expense
    }

def attendance_percentage(
    db: Session,
    clinic_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    filters = [
        Appointment.clinic_id == clinic_id,
        Appointment.status.in_([
            AppointmentStatus.REALIZADO.value,
            AppointmentStatus.FALTOU.value,
        ])
    ]

    if start_date:
        filters.append(Appointment.appointment_date >= start_date)

    if end_date:
        filters.append(Appointment.appointment_date <= end_date)

    result = (
        db.query(
            func.sum(
                case(
                    (Appointment.status == AppointmentStatus.REALIZADO.value, 1),
                    else_=0
                )
            ).label("realized"),

            func.sum(
                case(
                    (Appointment.status == AppointmentStatus.FALTOU.value, 1),
                    else_=0
                )
            ).label("absent")
        )
        .filter(*filters)
        .one()
    )

    total = result.realized + result.absent

    return {
        "attendance_percentage": (
            round(result.realized / total * 100, 2)
            if total > 0
            else 0
        )
    }