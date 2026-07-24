from pydantic import BaseModel, Field, field_validator
from schemas.dentist_schedule import ScheduleItem
from enums.DentistStatus import DentistStatus


# Essa função é usada para normalizar o valor do status antes de ser validado pelo Pydantic. Ela verifica se o valor é uma instância de DentistStatus, uma string que corresponde a um valor válido do enum, ou uma string que corresponde a um nome de membro do enum. Se o valor não puder ser normalizado, ele é retornado como está.
def _normalize_status_value(v):
    if isinstance(v, DentistStatus):
        return v

    if isinstance(v, str):
        raw = v.strip()
        if not raw:
            return v

        value_map = {member.value: member.value for member in DentistStatus}
        if raw in value_map:
            return raw

        enum_lookup = {member.name: member.value for member in DentistStatus}
        normalized = enum_lookup.get(raw.upper())
        if normalized:
            return normalized

        uppercase_lookup = {member.value.upper(): member.value for member in DentistStatus}
        return uppercase_lookup.get(raw.upper(), raw)

    return v


class DentistCreate(BaseModel):
    name: str
    email: str
    phone: str
    cpf: str
    cro: str
    specialties: list[str] = Field(default_factory=list)  # nomes; o service resolve/cria as linhas em Specialty
    status: DentistStatus = DentistStatus.ATIVO

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, v):
        return _normalize_status_value(v)
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

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, v):
        return _normalize_status_value(v)
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

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, v):
        return _normalize_status_value(v)


class DentistResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    cro: str
    specialties: list[str] = Field(default_factory=list)
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
    cpf_hash: str
    cpf_masked: str          
    specialties: list[str] = Field(default_factory=list)
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