from datetime import date
from typing import Optional
from models import *
from enums.ReceivableStatus import ReceivableStatus
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case, cast, Date, extract
from models.appointment import AppointmentStatus
from models.associations.appointment_procedure import AppointmentProcedure
from datetime import date, timedelta
from typing import Literal

Granularity = Literal["day", "month"]
 
 
def _add_month(d: date, months: int = 1) -> date:
    '''Realiza uma soma ou subtração dos meses, retorna o dia 1 do mês resultante'''
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)
 
 
def fill_days(results, start_date: date, end_date: date, value_field: str) -> list:
    '''Preenche com 0 os dias sem registros, impedindo buracos no gráfico.
    Cada linha de results precisa ter os campos "date" e value_field.'''
    values = {}
    for row in results:
        d = row.date
        if hasattr(d, "date") and callable(getattr(d, "date")):
            d = d.date()
        values[d] = getattr(row, value_field)

    filled = []
    current = start_date
    while current <= end_date:
        filled.append({"date": current, value_field: values.get(current, 0)})
        current = current + timedelta(days=1)

    return filled


def fill_months(results, start_date: date, end_date: date, value_field: str) -> list:
    '''Preenche com 0 os meses sem registros, impedindo buracos no gráfico.
    Cada linha de results precisa ter os campos "year", "month" e value_field.'''
    values = {}
    for row in results:
        values[(int(row.year), int(row.month))] = getattr(row, value_field)

    filled = []
    year = start_date.year
    month = start_date.month
    while (year, month) <= (end_date.year, end_date.month):
        filled.append({
            "year": year,
            "month": month,
            value_field: values.get((year, month), 0),
        })
        month = month + 1
        if month == 13:
            month = 1
            year = year + 1

    return filled

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
    granularity: Granularity = "month",
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = _add_month(end_date.replace(day=1), -11)

    filters = [
        Receivable.clinic_id == clinic_id,
        Receivable.status == ReceivableStatus.PAGO.value,
        Receivable.paid_at >= start_date,
        Receivable.paid_at <= end_date,
    ]

    if granularity == "day":
        group_cols = [cast(Receivable.paid_at, Date).label("date")]
    elif granularity == "month":
        group_cols = [
            extract("year", Receivable.paid_at).label("year"),
            extract("month", Receivable.paid_at).label("month"),
        ]
    else:
        raise ValueError(f"Granularidade inválida: {granularity}")

    results = (
        db.query(*group_cols, func.sum(Receivable.total_amount).label("total_revenue"))
        .filter(*filters)
        .group_by(*group_cols)
        .all()
    )

    if granularity == "day":
        return fill_days(results, start_date, end_date, "total_revenue")
    return fill_months(results, start_date, end_date, "total_revenue")

#gráfico de linhas/área que vai juntar com receita
def expense_by_month_billing(
    db: Session,
    clinic_id: str,
    granularity: Granularity = "month",
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = _add_month(end_date.replace(day=1), -11)

    filters = [
        Expense.clinic_id == clinic_id,
        Expense.status == "pago",
        Expense.paid_at >= start_date,
        Expense.paid_at <= end_date,
    ]

    if granularity == "day":
        group_cols = [cast(Expense.paid_at, Date).label("date")]
    elif granularity == "month":
        group_cols = [
            extract("year", Expense.paid_at).label("year"),
            extract("month", Expense.paid_at).label("month"),
        ]
    else:
        raise ValueError(f"Granularidade inválida: {granularity}")

    results = (
        db.query(*group_cols, func.sum(Expense.amount).label("total_expense"))
        .filter(*filters)
        .group_by(*group_cols)
        .all()
    )

    if granularity == "day":
        return fill_days(results, start_date, end_date, "total_expense")
    return fill_months(results, start_date, end_date, "total_expense")

#Controle appointments
#gráfico de rosca de atendimentos por status
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

#gráfico de rosca de despesas por categoria
def expenses_count(
    db: Session,
    clinic_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    filters = [Expense.clinic_id == clinic_id]
    if start_date:
        filters.append(Expense.due_date >= start_date)
    if end_date:
        filters.append(Expense.due_date <= end_date)

    results = (
        db.query(
            Expense.category.label("expense_category"),
            func.count(Expense.id).label("count")
        )

        .filter(*filters)
        .group_by(Expense.category)
        .all()
    )

    total = sum(row.count for row in results)

    return [
        {
            "category": row.expense_category,
            "count": row.count,
            "percentage": round((row.count / total) * 100, 2) if total > 0 else 0,
        }
        for row in results
    ]

#Gráfico de linha
def appointments_count_by_period(
    db: Session,
    clinic_id: str,
    granularity: Granularity = "month",
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = _add_month(end_date.replace(day=1), -11)

    filters = [
        Appointment.clinic_id == clinic_id,
        Appointment.status == AppointmentStatus.REALIZADO.value,
        Appointment.appointment_date >= start_date,
        Appointment.appointment_date <= end_date,
    ]

    if granularity == "day":
        group_cols = [cast(Appointment.appointment_date, Date).label("date")]
    elif granularity == "month":
        group_cols = [
            extract("year", Appointment.appointment_date).label("year"),
            extract("month", Appointment.appointment_date).label("month"),
        ]
    else:
        raise ValueError(f"Granularidade inválida: {granularity}")

    results = (
        db.query(*group_cols, func.count(Appointment.id).label("count"))
        .filter(*filters)
        .group_by(*group_cols)
        .all()
    )

    if granularity == "day":
        return fill_days(results, start_date, end_date, "count")
    return fill_months(results, start_date, end_date, "count")

def dentists_daily_appointments(
    db: Session,
    clinic_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = _add_month(end_date.replace(day=1), -11)

    filters = [
        Appointment.clinic_id == clinic_id,
        Appointment.status == AppointmentStatus.REALIZADO.value,
        Appointment.appointment_date >= start_date,
        Appointment.appointment_date <= end_date,
    ]

    results = (
        db.query(
            Appointment.appointment_date.label("date"),
            func.count(Appointment.id).label("count")
        )
        .filter(*filters)
        .group_by(Appointment.appointment_date)
        .all()
    )

    return fill_days(results, start_date, end_date, "count")


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
        Expense.clinic_id == clinic_id,
        Expense.status == "pago",
        Expense.paid_at.isnot(None),
    ]

    if start_date:
        revenue_filters.append(Receivable.paid_at >= start_date)
        expense_filters.append(Expense.paid_at >= start_date)

    if end_date:
        revenue_filters.append(Receivable.paid_at <= end_date)
        expense_filters.append(Expense.paid_at <= end_date)

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


#gráfico de linha
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
            func.coalesce(
                func.sum(
                    case(
                        (Appointment.status == AppointmentStatus.REALIZADO.value, 1),
                        else_=0
                    )
                ),
                0
            ).label("realized"),

            func.coalesce(
                func.sum(
                    case(
                        (Appointment.status == AppointmentStatus.FALTOU.value, 1),
                        else_=0
                    )
                ),
                0
            ).label("absent")
        )
        .filter(*filters)
        .one()
    )

    realized = result.realized or 0
    absent = result.absent or 0
    total = realized + absent

    return {
        "attendance_percentage": (
            round(realized / total * 100, 2)
            if total > 0
            else 0
        ),
        "total": total
    }