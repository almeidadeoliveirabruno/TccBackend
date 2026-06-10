from sqlalchemy.orm import Session

from models.clinic import Clinic


def get_clinic_by_cnpj(
    db: Session,
    cnpj: str
):

    return db.query(Clinic).filter(
        Clinic.cnpj == cnpj
    ).first()


def create_clinic(
    db: Session,
    nome: str,
    cnpj: str
):

    clinic = Clinic(
        nome=nome,
        cnpj=cnpj,
    )

    if get_clinic_by_cnpj(db,cnpj):
        raise ValueError("Clínica já cadastrada")

    db.add(clinic)
    db.flush()

    return clinic