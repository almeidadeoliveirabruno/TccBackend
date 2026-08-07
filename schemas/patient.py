from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


def validate_birth_date(birth_date: str) -> str:
    try:
        parsed_date = datetime.strptime(birth_date, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("A data de nascimento deve estar no formato YYYY-MM-DD") from exc

    if parsed_date > date.today():
        raise ValueError("A data de nascimento não pode ser no futuro")

    return birth_date


class PatientCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    cpf: str
    birth_date: str
    gender: str
    observations: str | None = None
    health_plan: str | None = None
    profession: str | None = None
    street: str
    number: str
    complement: str | None = None
    neighborhood: str
    city: str
    state: str
    cep: str

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date_field(cls, value: str) -> str:
        return validate_birth_date(value)


class PatientUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    cpf: str | None = None
    birth_date: str | None = None
    gender: str | None = None
    observations: str | None = None
    health_plan: str | None = None
    profession: str | None = None
    street: str | None = None
    number: str | None = None
    complement: str | None = None
    neighborhood: str | None = None
    city: str | None = None
    state: str | None = None
    cep: str | None = None

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date_field(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return validate_birth_date(value)


class PatientResponseCard(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str
    email: str | None = None


class PatientResponseDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    phone: str
    cpf: str
    birth_date: str
    gender: str
    observations: str | None = None
    health_plan: str | None = None
    profession: str | None = None
    street: str
    number: str
    complement: str | None = None
    neighborhood: str
    city: str
    state: str
    cep: str

class PatientSummaryAppointment(BaseModel):
    appointment_id: int
    date: date
    time_begin: str
    time_end: str
    dentist: str


class PatientSummaryResponse(BaseModel):
    last_consult: PatientSummaryAppointment | None
    next_consult: PatientSummaryAppointment | None

class PatientHistoryProcedure(BaseModel):
    id: int  # AppointmentProcedure.id — usado pelo front pra editar o dente (FDI) individualmente
    name: str
    tooth: str | None
    display: str


class PatientHistoryAppointment(BaseModel):
    appointment_id: int
    date: date
    time_begin: str
    time_end: str
    dentist: str
    notes: str | None
    procedures: list[PatientHistoryProcedure]