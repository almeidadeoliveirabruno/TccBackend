from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import os
import hashlib
from dotenv import load_dotenv

pwd_context = CryptContext(
    schemes=["bcrypt_sha256"],
    deprecated="auto"
)

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(
        plain_password,
        hashed_password
    )

def hash_password(password: str):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(
        timezone.utc
    ) + timedelta(minutes=30)

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

from cryptography.fernet import Fernet, InvalidToken
 
# --- Hash para duplicidade/busca (determinístico, NÃO reversível) ---
CPF_PEPPER = os.getenv("CPF_HASH_PEPPER", "change-this-pepper-in-env")
 
# --- Criptografia reversível (para exibir o CPF de volta quando necessário) ---
# Gere uma chave com:
#   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# e guarde em CPF_ENCRYPTION_KEY (variável de ambiente / secrets manager).
# Trocar essa chave em produção invalida todos os CPFs já criptografados
# no banco — se isso acontecer, decrypt_cpf() retorna "***" em vez de quebrar.
_CPF_ENCRYPTION_KEY = os.getenv("CPF_ENCRYPTION_KEY")
if not _CPF_ENCRYPTION_KEY:
    # Fallback só pra dev local. Em produção, isso TEM que vir do ambiente.
    _CPF_ENCRYPTION_KEY = Fernet.generate_key().decode()
 
_fernet = Fernet(_CPF_ENCRYPTION_KEY.encode())
 
 
def _only_digits(cpf: str) -> str:
    return "".join(filter(str.isdigit, cpf))
 
 
def hash_cpf(cpf: str) -> str:
    """
    Hash determinístico (SHA-256 + pepper) usado SÓ para checar duplicidade
    e buscar por CPF exato (WHERE cpf_hash = ...). Não é reversível.
    """
    return hashlib.sha256(f"{_only_digits(cpf)}{CPF_PEPPER}".encode()).hexdigest()
 
 
def encrypt_cpf(cpf: str) -> str:
    """Criptografia reversível (Fernet/AES) do CPF, para exibir de volta na UI."""
    return _fernet.encrypt(_only_digits(cpf).encode()).decode()
 
 
def decrypt_cpf(encrypted_cpf: str) -> str:
    """Descriptografa o CPF armazenado. Retorna '***' se a chave mudou ou o dado
    estiver corrompido, em vez de derrubar a aplicação."""
    try:
        return _fernet.decrypt(encrypted_cpf.encode()).decode()
    except InvalidToken:
        return "***"
 
 
def mask_cpf(cpf: str) -> str:
    """Formata CPF mascarado para exibição em listagens: 123.***.**9-00"""
    digits = _only_digits(cpf)
    if len(digits) != 11:
        return "***.***.***-**"
    return f"{digits[:3]}.***.**{digits[8]}-{digits[9:]}"
 