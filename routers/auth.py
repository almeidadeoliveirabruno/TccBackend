from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session
from fastapi import HTTPException
from db.dependencies import get_db, get_current_user
from models.user import User
from schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserProfileResponse,
    UserProfileUpdate,
    UserProfileUpdateResponse,
)
from schemas.token import Token
from services.auth_service import (
    get_user,
    create_user,
    authenticate_user,
    update_user_profile,
)
from core.security import create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Usuário já existe")
    return create_user(db, user)

@router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = authenticate_user(db, user.email, user.password)
    if not db_user:
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")

    access_token = create_access_token({"sub": db_user.email, "clinic_id": db_user.clinic_id, "nome": db_user.nome})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserProfileResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user

@router.put("/me", response_model=UserProfileUpdateResponse)
def update_my_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    updated_user = update_user_profile(
        db=db,
        user=current_user,
        nome=profile_data.nome,
        nome_clinica=profile_data.nome_clinica,
        cnpj=profile_data.cnpj
    )

    access_token = create_access_token({
        "sub": updated_user.email,
        "clinic_id": updated_user.clinic_id,
        "nome": updated_user.nome
    })

    return {
        "id": updated_user.id,
        "email": updated_user.email,
        "nome": updated_user.nome,
        "clinic": updated_user.clinic,
        "access_token": access_token,
        "token_type": "bearer"
    }

