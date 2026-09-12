from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.security import hash_password, verify_password
from models.user import User
from schemas.user import UserCreate
from services.clinic_service import create_clinic


def get_user(
    db: Session,
    email: str
):
    return db.query(User).filter(
        User.email == email
    ).first()


def _validar_senha(senha: str) -> str:
    if not senha or len(senha) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Senha deve ter no mínimo 8 caracteres"
        )
    return senha


def create_user(db: Session, user: UserCreate):
    email = (user.email or "").strip().lower()
    if not email:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="E-mail é obrigatório"
        )

    nome = (user.nome or "").strip()
    if not nome:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nome é obrigatório"
        )

    _validar_senha(user.password)

    # Verifica duplicidade de e-mail ANTES de criar a clínica,
    # pra evitar criar uma clínica "órfã" caso o e-mail já exista.
    if get_user(db, email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já cadastrado"
        )

    clinic = create_clinic(db, user.clinic)

    db_user = User(
        email=email,
        hashed_password=hash_password(user.password),
        clinic_id=clinic.id,
        nome=nome
    )

    db.add(db_user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já cadastrado"
        )

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