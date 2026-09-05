from models import *
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case
from datetime import date
from enums.ExpenseStatus import ExpenseStatus
from enums.DentistStatus import DentistStatus
from models.appointment import AppointmentStatus

def last_five_patients(
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
def next_appointment_by_dentist(
    db: Session,
    clinic_id: str
):
    dentists = (
        db.query(Dentist)
        .filter(
            Dentist.clinic_id == clinic_id,
            Dentist.status == DentistStatus.ATIVO
        )
        .all()
    )

    result = []

    for dentist in dentists:
        appointment = (
            db.query(Appointment)
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
            .first()
        )

        result.append({
            "dentist": dentist,
            "appointment": appointment
        })

    return result