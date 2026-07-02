from pydantic import BaseModel
from enums.ProcedureCategory import ProcedureCategory


class ProcedureCreate(BaseModel):
    name: str
    category: ProcedureCategory
    price: float
    duration: int | None = None
    description: str | None = None
    

class ProcedureUpdate(BaseModel):
    name: str | None = None
    category: ProcedureCategory | None = None
    price: float | None = None
    duration: int | None = None
    description: str | None = None
    

class ProcedureResponse(BaseModel):
    id: int
    name: str
    category: ProcedureCategory
    price: float
    duration: int | None
    description: str | None

#class config é necessária para que o pydantic possa criar um modelo a partir de um objeto SQLAlchemy, permitindo que os dados sejam convertidos corretamente entre os dois formatos. Sem a necessidade de criar um dicionário intermediário, o pydantic pode acessar diretamente os atributos do objeto SQLAlchemy para preencher os campos do modelo de resposta.
    class Config:
        from_attributes = True

class ProcedurePaginatedResponse(BaseModel):
    items: list[ProcedureResponse]
    page: int
    page_size: int
    total: int
    total_pages: int
    statistics: dict[str, float | int]

    class Config:
        from_attributes = True
