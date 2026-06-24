from sqlalchemy.orm import Session
from models.clinic import Clinic
from schemas.clinic import ClinicCreate


def get_clinic_by_cnpj(
    db: Session,
    cnpj: str
):

    return db.query(Clinic).filter(
        Clinic.cnpj == cnpj
    ).first()


def create_clinic(
    db: Session,
    clinic_create: ClinicCreate
):

    clinic = Clinic(
        nome=clinic_create.nome,
        cnpj=clinic_create.cnpj,
    )

    if get_clinic_by_cnpj(db, clinic_create.cnpj):
        raise ValueError("Clínica já cadastrada")

    db.add(clinic)
    db.flush()

    return clinic