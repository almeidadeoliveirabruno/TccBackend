from pydantic import BaseModel, field_validator
from schemas.dentist_schedule import ScheduleItem
from models.dentist import DentistStatus


class DentistCreate(BaseModel):
    name: str
    email: str
    phone: str
    cpf: str
    cro: str
    specialties: list[str] = []  # nomes; o service resolve/cria as linhas em Specialty
    status: DentistStatus = DentistStatus.ATIVO
    street: str
    number: str
    complement: str | None = None
    neighborhood: str
    city: str
    state: str
    cep: str
    schedules: list[ScheduleItem] | None = None


class DentistUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    cro: str | None = None
    specialties: list[str] | None = None
    status: DentistStatus | None = None
    street: str | None = None
    number: str | None = None
    complement: str | None = None
    neighborhood: str | None = None
    city: str | None = None
    state: str | None = None
    cep: str | None = None


class DentistStatusUpdate(BaseModel):
    """Schema enxuto pra rota dedicada de troca de status (PATCH /dentists/{id}/status)."""
    status: DentistStatus


class DentistResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    cro: str
    specialties: list[str] = []
    status: DentistStatus
    cpf_masked: str

    # O relationship `specialties` do model retorna objetos Specialty, nao
    # strings. Esse validator converte antes da validacao do Pydantic.
    # o before serve para que o validator seja chamado antes da validacao do pydantic, para que possamos manipular os dados antes de serem validados.
    @field_validator("specialties", mode="before")
    @classmethod
    def extract_specialty_names(cls, v):
        if v and hasattr(v[0], "name"):
            return [s.name for s in v]
        return v or []

    class Config:
        from_attributes = True


class DentistResponseDetail(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    cro: str
    cpf: str
    specialties: list[str] = []
    status: DentistStatus
    street: str
    number: str
    complement: str | None = None
    neighborhood: str
    city: str
    state: str
    cep: str

    @field_validator("specialties", mode="before")
    @classmethod
    def extract_specialty_names(cls, v):
        if v and hasattr(v[0], "name"):
            return [s.name for s in v]
        return v or []

    class Config:
        from_attributes = True