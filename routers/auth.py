from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session
from fastapi import HTTPException
from db.dependencies import get_db
from schemas.user import UserCreate, UserLogin, UserResponse
from schemas.token import Token
from services.auth_service import (
    get_user,
    create_user,
    authenticate_user
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
