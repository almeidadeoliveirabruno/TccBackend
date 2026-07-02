from pydantic import BaseModel

class DentistCreate(BaseModel):
    name: str
    cpf: str
    cro: str
    specialty: str
    street: str
    number: str
    complement: str | None = None
    neighborhood: str
    city: str
    state: str
    cep: str

class DentistResponse(BaseModel):
    id: int
    name: str
    cpf: str
    cro: str
    specialty: str | None = None

    class Config:
        orm_mode = True

class DentistResponseDetail(BaseModel):
    id: int
    name: str
    cpf: str
    cro: str
    specialty: str | None = None
    street: str
    number: str
    complement: str | None = None
    neighborhood: str
    city: str
    state: str
    cep: str

    class Config:
        orm_mode = True