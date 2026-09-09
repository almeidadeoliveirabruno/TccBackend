from models import *
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, case
from datetime import date
from enums.ExpenseStatus import ExpenseStatus
from enums.DentistStatus import DentistStatus
from models.appointment import AppointmentStatus
from schemas.home import NextAppointmentsByDentist, AppointmentSummary, ProcedureCategoryDistribution

def last_patients(
    db: Session,
    clinic_id: str
):
    results = db.query(Patient).filter(Patient.clinic_id == clinic_id).order_by(Patient.created_at.desc()).limit(5)
    return results


#cards
def patients_count(
    db: Session,
    clinic_id: str
):
    count = db.query(func.count(Patient.id).label('patients_count')).filter(Patient.clinic_id == clinic_id).scalar()
    return {"patients_count": count}

def appointments_today(
    db: Session,
    clinic_id: str
):
    count = db.query(func.count(Appointment.id)).filter(Appointment.appointment_date == date.today(), Appointment.clinic_id == clinic_id).scalar()
    return {'appointments_count' : count}

def expenses_not_paid(
    db: Session,
    clinic_id: str    
):
    count = db.query(func.count(Expense.id)).filter(Expense.clinic_id == clinic_id, Expense.status == ExpenseStatus.PENDENTE).scalar()
    return {'expense_count' : count}

def total_active_dentists(
    db: Session,
    clinic_id: str 
):
    count = db.query(func.count(Dentist.id)).filter(Dentist.clinic_id == clinic_id, Dentist.status ==  DentistStatus.ATIVO).scalar()
    return {'dentist_count' : count}

#Mostra os agendamentos que estão com status agendado e que já passaram da data de agendamento, ou seja, o status não foi atualizado para realizado, cancelado ou faltou.
def pending_appointments(
    db: Session,
    clinic_id: str, 
    dentist_id: str
):
    appointments = db.query(
        Appointment.dentist,
        Appointment.status, 
        Appointment.time_begin,
        Appointment.patient
        ).filter(
        Appointment.clinic_id == clinic_id, 
        Appointment.status == AppointmentStatus.AGENDADO,
        Appointment.dentist_id == dentist_id,
        Appointment.appointment_date < date.today()
        ).order_by(Appointment.appointment_date.desc()).all()

    return appointments

# Próximos agendamentos de cada dentista, considerando apenas os agendamentos com status agendado ou confirmado.
def get_next_appointments_by_dentist(
    db: Session,
    clinic_id: str,
    dentist_id: int,
) -> NextAppointmentsByDentist | None:
    dentist = (
        db.query(Dentist)
        .filter(
            Dentist.id == dentist_id,
            Dentist.clinic_id == clinic_id,
            Dentist.status == DentistStatus.ATIVO
        )
        .first()
    )

    if dentist is None:
        return None

    appointments = (
        db.query(Appointment)
        .options(
            joinedload(Appointment.patient),
            joinedload(Appointment.procedure_items)
                .joinedload(AppointmentProcedure.procedure),
        )
        .filter(
            Appointment.clinic_id == clinic_id,
            Appointment.dentist_id == dentist.id,
            Appointment.appointment_date >= date.today(),
            Appointment.status.in_([
                AppointmentStatus.AGENDADO,
                AppointmentStatus.CONFIRMADO
            ])
        )
        .order_by(
            Appointment.appointment_date.asc(),
            Appointment.time_begin.asc()
        )
        .limit(5)
        .all()
    )

    return NextAppointmentsByDentist(
        dentist_name=dentist.name,
        appointments=[
            AppointmentSummary(
                patient_name=appt.patient.name,
                procedure_name=[
                    item.procedure.name
                    for item in appt.procedure_items
                ],
                appointment_date=appt.appointment_date,
                time_begin=appt.time_begin,
                time_end=appt.time_end,
                appointment_status=appt.status,
            )
            for appt in appointments
        ],
    )

def procedures_category_distribution(
    db: Session,
    clinic_id: str
) -> list[ProcedureCategoryDistribution]:
    results = (
        db.query(
            Procedure.category.label("category_name"),
            func.count(AppointmentProcedure.id).label("procedure_count"),
        )
        .join(AppointmentProcedure, AppointmentProcedure.procedure_id == Procedure.id)
        .join(Appointment, Appointment.id == AppointmentProcedure.appointment_id)
        .filter(Appointment.clinic_id == clinic_id)
        .group_by(Procedure.category)
        .order_by(func.count(AppointmentProcedure.id).desc())
        .all()
    )

    total = sum(r.procedure_count for r in results)

    if total == 0:
        return []

    top_4 = results[:4]
    rest = results[4:]

    distribution = [
        ProcedureCategoryDistribution(
            category_name=r.category_name,
            percentage=round((r.procedure_count / total) * 100, 1),
        )
        for r in top_4
    ]

    if rest:
        rest_count = sum(r.procedure_count for r in rest)
        distribution.append(
            ProcedureCategoryDistribution(
                category_name="Demais categorias",
                percentage=round((rest_count / total) * 100, 1),
            )
        )

    return distribution