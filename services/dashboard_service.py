from datetime import date
from typing import Optional
from models import *
from enums.ReceivableStatus import ReceivableStatus
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case, cast, Date
from models.appointment import AppointmentStatus
from models.associations.appointment_procedure import AppointmentProcedure
from datetime import date, timedelta
from typing import Literal

Granularity = Literal["day", "week", "month"]
 
 
def _week_start(d: date) -> date:
    '''A função retorna a data da segunda feira daquela semana'''
    return d - timedelta(days=d.weekday())
 
 
def _add_month(d: date, months: int = 1) -> date:
    '''Realiza uma soma ou subtração dos meses, retorna o dia 1 do mês resultante'''
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)
 
 
def generate_periods(
    start_date: date,
    end_date: date,
    granularity: Granularity = "month",
) -> list:
    '''Gera as datas faltantes, impedindo problemas no gráfico'''
    periods = []
 
    if granularity == "day":
        current = start_date
        while current <= end_date:
            periods.append(current)
            current += timedelta(days=1)
 
    elif granularity == "week":
        current = _week_start(start_date)
        last_week = _week_start(end_date)
        while current <= last_week:
            periods.append(current)
            current += timedelta(weeks=1)
 
    elif granularity == "month":
        current = start_date.replace(day=1)
        last_month = end_date.replace(day=1)
        while current <= last_month:
            periods.append((current.year, current.month))
            current = _add_month(current)
 
    else:
        raise ValueError(f"Granularidade inválida: {granularity}")
 
    return periods
 
 
def fill_missing_periods(
    results,
    start_date: date,
    end_date: date,
    granularity: Granularity,
    key_fn,
    build_row_fn,
    empty_row_fn,
):
    periods = generate_periods(start_date, end_date, granularity)
    index = {key_fn(row): row for row in results}
 
    filled = []
    for period in periods:
        row = index.get(period)
        if row is not None:
            filled.append(build_row_fn(period, row))
        else:
            filled.append(empty_row_fn(period))
 
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
        receivable_conditions.append(cast(Receivable.paid_at, Date) >= start_date)
    if end_date:
        receivable_conditions.append(cast(Receivable.paid_at, Date) <= end_date)

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
        receivable_conditions.append(cast(Receivable.paid_at, Date) >= start_date)
    if end_date:
        receivable_conditions.append(cast(Receivable.paid_at, Date) <= end_date)

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
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = _add_month(end_date.replace(day=1), -11)

    filters = [
        Receivable.clinic_id == clinic_id,
        Receivable.status == ReceivableStatus.PAGO.value,
        cast(Receivable.paid_at, Date) >= start_date,
        cast(Receivable.paid_at, Date) <= end_date,
    ]

    results = (
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

    return fill_missing_periods(
        results=results,
        start_date=start_date,
        end_date=end_date,
        granularity="month",
        key_fn=lambda row: (row.year, row.month),
        build_row_fn=lambda period, row: {
            "year": period[0],
            "month": period[1],
            "total_revenue": row.total_revenue,
        },
        empty_row_fn=lambda period: {
            "year": period[0],
            "month": period[1],
            "total_revenue": 0,
        },
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

    if granularity == "month":
        group_cols = [
            func.year(Appointment.appointment_date).label("year"),
            func.month(Appointment.appointment_date).label("month"),
        ]
        key_fn = lambda row: (row.year, row.month)
        build_row_fn = lambda period, row: {"year": period[0], "month": period[1], "count": row.count}
        empty_row_fn = lambda period: {"year": period[0], "month": period[1], "count": 0}

    elif granularity == "day":
        group_cols = [Appointment.appointment_date.label("appointment_date")]
        key_fn = lambda row: row.appointment_date
        build_row_fn = lambda period, row: {"date": period, "count": row.count}
        empty_row_fn = lambda period: {"date": period, "count": 0}

    else:
        raise ValueError(f"Granularidade inválida: {granularity}")

    results = (
        db.query(*group_cols, func.count(Appointment.id).label("count"))
        .filter(*filters)
        .group_by(*group_cols)
        .order_by(*group_cols)
        .all()
    )

    return fill_missing_periods(
        results=results,
        start_date=start_date,
        end_date=end_date,
        granularity=granularity,
        key_fn=key_fn,
        build_row_fn=build_row_fn,
        empty_row_fn=empty_row_fn,
    )

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
            Appointment.appointment_date.label("appointment_date"),
            func.count(Appointment.id).label("count")
        )
        .filter(*filters)
        .group_by(Appointment.appointment_date)
        .order_by(Appointment.appointment_date)
        .all()
    )

    return fill_missing_periods(
        results=results,
        start_date=start_date,
        end_date=end_date,
        granularity="day",
        key_fn=lambda row: row.appointment_date,
        build_row_fn=lambda period, row: {
            "date": period,
            "count": row.count,
        },
        empty_row_fn=lambda period: {
            "date": period,
            "count": 0,
        },
    )


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
        revenue_filters.append(cast(Receivable.paid_at, Date) >= start_date)
        expense_filters.append(Expense.due_date >= start_date)

    if end_date:
        revenue_filters.append(cast(Receivable.paid_at, Date) <= end_date)
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
        ),
        "total": total
    }