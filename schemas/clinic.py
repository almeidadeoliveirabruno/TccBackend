from pydantic import BaseModel

class ClinicCreate(BaseModel):
    nome: str
    cnpj: str