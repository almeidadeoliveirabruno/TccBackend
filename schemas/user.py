from pydantic import BaseModel
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
    nome:str

    class Config:
        orm_mode = True
