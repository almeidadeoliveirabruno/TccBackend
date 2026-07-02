from sqlalchemy.orm import Session
from models.dentist import Dentist
from passlib.context import CryptContext
from schemas.dentist import DentistCreate, DentistResponseDetail, DentistResponse
from fastapi import HTTPException


def hash_cpf(cpf: str) -> str:
    pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")
    return pwd_context.hash(cpf)

def create_dentist(
    db: Session,
    dentist_create: DentistCreate,
    clinic_id: int
): 
    # Verificar se o dentista já existe nesta clínica com base no CPF
    existing_dentist = db.query(Dentist).filter(
        Dentist.cpf == hash_cpf(dentist_create.cpf),
        Dentist.clinic_id == clinic_id
    ).first()

    if existing_dentist:
        raise HTTPException(
            status_code=409,  
            detail="Já existe um dentista com esse CPF cadastrado nesta clínica"
        )

    dentist = Dentist(
        name=dentist_create.name.title(),
        cpf=hash_cpf(dentist_create.cpf),
        email=dentist_create.email,
        phone=dentist_create.phone,
        clinic_id=clinic_id,
        cro=dentist_create.cro,
        specialty=dentist_create.specialty,
        street=dentist_create.street,
        number=dentist_create.number,
        complement=dentist_create.complement,
        neighborhood=dentist_create.neighborhood,
        city=dentist_create.city,
        state=dentist_create.state,
        cep=dentist_create.cep
    )

    db.add(dentist)

    return dentist
       

def get_dentists_by_clinic_id_page(
    db: Session,
    clinic_id: int,
    page: int = 1,
    page_size: int = 10
):
    skip = (page - 1) * page_size

    dentists = (
        db.query(Dentist)
        .filter(Dentist.clinic_id == clinic_id)
        .offset(skip)
        .limit(page_size)
        .all()
    )

    return dentists
