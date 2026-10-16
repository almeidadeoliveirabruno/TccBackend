from pydantic import BaseModel, ConfigDict
from schemas.clinic import ClinicCreate

class UserCreate(BaseModel):
    email: str
    password: str
    clinic: ClinicCreate
    nome: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    clinic: ClinicCreate
    nome: str

    model_config = ConfigDict(from_attributes=True)

class ClinicResponse(BaseModel):
    id: str
    nome: str
    cnpj: str

    model_config = ConfigDict(from_attributes=True)

class UserProfileResponse(BaseModel):
    id: int
    email: str
    nome: str
    clinic: ClinicResponse

    model_config = ConfigDict(from_attributes=True)

class UserProfileUpdate(BaseModel):
    nome: str
    nome_clinica: str
    cnpj: str

class UserProfileUpdateResponse(BaseModel):
    id: int
    email: str
    nome: str
    clinic: ClinicResponse
    access_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(from_attributes=True)

