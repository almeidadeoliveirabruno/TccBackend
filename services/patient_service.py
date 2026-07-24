from datetime import date, datetime
import math

from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException

from models.patient import Patient
from schemas.patient import (
    PatientCreate,
    PatientUpdate,
    PatientResponseCard,
    PatientResponseDetail,
)
from core.security import hash_cpf, encrypt_cpf, decrypt_cpf


def validate_birth_date_not_future(birth_date: str) -> None:
    try:
        parsed_date = datetime.strptime(birth_date, "%Y-%m-%d").date()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="A data de nascimento deve estar no formato YYYY-MM-DD") from exc

    if parsed_date > date.today():
        raise HTTPException(status_code=422, detail="A data de nascimento não pode ser no futuro")


def _to_patient_detail(patient: Patient, cpf_plain: str | None = None) -> PatientResponseDetail:
    """Monta a resposta de detalhe, descriptografando o CPF quando não veio pronto."""
    cpf = cpf_plain if cpf_plain is not None else decrypt_cpf(patient.cpf_encrypted)
    return PatientResponseDetail(
        id=patient.id,
        name=patient.name,
        email=patient.email,
        phone=patient.phone,
        cpf=cpf,
        birth_date=patient.birth_date,
        gender=patient.gender,
        observations=patient.observations,
        health_plan=patient.health_plan,
        profession=patient.profession,
        street=patient.street,
        number=patient.number,
        complement=patient.complement,
        neighborhood=patient.neighborhood,
        city=patient.city,
        state=patient.state,
        cep=patient.cep,
    )


def create_patient(
    db: Session,
    patient_create: PatientCreate,
    clinic_id: str
) -> PatientResponseDetail:
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

    # já temos o CPF em mãos (patient_create.cpf), não precisa descriptografar de novo
    return _to_patient_detail(patient, cpf_plain=patient_create.cpf)


def get_patient_by_id(db: Session, patient_id: int, clinic_id: str) -> Patient:
    """Retorna o objeto ORM cru. Usado internamente por update/delete/detail."""
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


def get_patient_detail(db: Session, patient_id: int, clinic_id: str) -> PatientResponseDetail:
    """Usado pela rota GET /{patient_id} — já vem com o CPF descriptografado."""
    patient = get_patient_by_id(db, patient_id, clinic_id)
    return _to_patient_detail(patient)


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
        "items": [PatientResponseCard.model_validate(p) for p in patients],
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
) -> PatientResponseDetail:
    patient = get_patient_by_id(db, patient_id, clinic_id)

    if patient_update.birth_date:
        validate_birth_date_not_future(patient_update.birth_date)

    data = patient_update.model_dump(exclude_unset=True)

    # se o CPF foi atualizado, recalcula hash e criptografado
    if "cpf" in data:
        new_cpf = data.pop("cpf")
        patient.cpf_hash = hash_cpf(new_cpf)
        patient.cpf_encrypted = encrypt_cpf(new_cpf)

    for field, value in data.items():
        setattr(patient, field, value)

    db.flush()

    return _to_patient_detail(patient)


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