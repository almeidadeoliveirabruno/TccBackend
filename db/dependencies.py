from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from jose import jwt, JWTError

from sqlalchemy.orm import Session

from db.database import SessionLocal

from core.security import (
    SECRET_KEY,
    ALGORITHM
)

from models.user import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)

# A função get_db é uma dependência que fornece uma sessão de banco de dados para as rotas que precisam acessar o banco. Ela cria uma sessão, a disponibiliza para a rota e garante que a sessão seja fechada após o uso, mesmo que ocorra um erro durante a operação.
def get_db():

    db = SessionLocal()

    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()

# A função get_current_user é uma dependência que extrai o token de acesso do cabeçalho da solicitação, decodifica o token para obter o nome de usuário e, em seguida, consulta o banco de dados para recuperar o usuário correspondente. Se o token for inválido ou se o usuário não for encontrado, a função levanta uma exceção HTTP 401 (Unauthorized).
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):

    credentials_exception = HTTPException(
        status_code=401,
        detail="Invalid credentials"
    )

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        email = payload.get("sub")

        if email is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(
        User.email == email
    ).first()

    if user is None:
        raise credentials_exception

    return user

def get_current_clinic_id(current_user: User = Depends(get_current_user)):
    return current_user.clinic_id