from pydantic import BaseModel
from typing import Optional

class EnderecoCreate(BaseModel):
    rua: str
    numero: str
    complemento: Optional[str] = None
    bairro: str
    cidade: str
    estado: str
    cep: str