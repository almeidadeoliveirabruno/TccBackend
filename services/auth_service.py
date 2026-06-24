from sqlalchemy.orm import Session
from schemas.user import UserCreate
from models.user import User
from services.clinic_service import create_clinic
from core.security import (
    hash_password,
    verify_password
)


def get_user(
    db: Session,
    email: str
):

    return db.query(User).filter(
        User.email == email
    ).first()


def create_user(db: Session, user: UserCreate):

    clinic = create_clinic(
        db,
        user.clinic
    )

    db_user = User(
        email=user.email,
        hashed_password=hash_password(user.password),
        clinic_id=clinic.id,
        nome=user.nome
    )

    db.add(db_user)
    db.flush()

    return db_user


def authenticate_user(
    db: Session,
    email: str,
    password: str
):

    user = get_user(
        db,
        email
    )

    if not user:
        return None

    if not verify_password(
        password,
        user.hashed_password
    ):
        return None

    return user