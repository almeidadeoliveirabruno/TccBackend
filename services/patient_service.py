from datetime import date, datetime
import math

from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException

from models.patient import Patient
from schemas.patient import PatientCreate, PatientUpdate
from core.security import hash_cpf, encrypt_cpf


def validate_birth_date_not_future(birth_date: str) -> None:
    try:
        parsed_date = datetime.strptime(birth_date, "%Y-%m-%d").date()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="A data de nascimento deve estar no formato YYYY-MM-DD") from exc

    if parsed_date > date.today():
        raise HTTPException(status_code=422, detail="A data de nascimento não pode ser no futuro")


def create_patient(
    db: Session,
    patient_create: PatientCreate,
    clinic_id: str
):
    validate_birth_date_not_future(patient_create.birth_date)

    cpf_hash = hash_cpf(patient_create.cpf)

    existing_patient = (
        db.query(Patient)
        .filter(Patient.cpf_hash == cpf_hash, Patient.clinic_id == clinic_id)
        .first()
    )
    if existing_patient:
        raise HTTPException(
            status_code=409,
            detail="Já existe um paciente com esse CPF cadastrado nesta clínica",
        )

    patient = Patient(
        name=patient_create.name.title(),
        email=patient_create.email,
        phone=patient_create.phone,
        cpf_hash=cpf_hash,
        cpf_encrypted=encrypt_cpf(patient_create.cpf),
        birth_date=patient_create.birth_date,
        gender=patient_create.gender,
        observations=patient_create.observations,
        health_plan=patient_create.health_plan,
        profession=patient_create.profession,
        street=patient_create.street,
        number=patient_create.number,
        complement=patient_create.complement,
        neighborhood=patient_create.neighborhood,
        city=patient_create.city,
        state=patient_create.state,
        cep=patient_create.cep,
        clinic_id=clinic_id
    )

    db.add(patient)
    db.flush()
    return patient

def get_patient_by_id(db: Session, patient_id: int, clinic_id: str) -> Patient:
    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id, Patient.clinic_id == clinic_id)
        .first()
    )
    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Paciente não encontrado nesta clínica",
        )
    return patient


def get_patients_by_clinic_id(
    db: Session,
    clinic_id: str,
    page: int = 1,
    page_size: int = 10,
    search: str | None = None,
):
    skip = (page - 1) * page_size

    query = db.query(Patient).filter(Patient.clinic_id == clinic_id)

    if search:
        like = f"%{search}%"
        query = query.filter(
            Patient.name.ilike(like)
        )

    total = query.count()

    patients = (
        query
        .order_by(Patient.name.asc())
        .offset(skip)
        .limit(page_size)
        .all()
    )

    return {
        "items": patients,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": max(1, math.ceil(total / page_size)) if total else 1,
        "statistics": {
            "total_patients": total
        }
    }

def update_patient(
    db: Session,
    patient_id: int,
    patient_update: PatientUpdate,
    clinic_id: str
):
    patient = get_patient_by_id(db, patient_id, clinic_id)

    if patient_update.birth_date:
        validate_birth_date_not_future(patient_update.birth_date)

    data = patient_update.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(patient, field, value)

    db.flush()

    return patient

def delete_patient(
    db: Session,
    patient_id: int,
    clinic_id: str
):
    patient = get_patient_by_id(db, patient_id, clinic_id)

    db.delete(patient)
    db.flush()

def search_patients(db: Session, search_query: str, clinic_id: str):
    return (
        db.query(Patient)
        .filter(
            Patient.clinic_id == clinic_id,
            (Patient.name.ilike(f"%{search_query}%"))
            | (Patient.cpf_encrypted.ilike(f"%{search_query}%")),
        )
        .all()
    )

