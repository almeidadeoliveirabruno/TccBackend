import re
from datetime import date, time

from pydantic import BaseModel, ConfigDict, field_validator

from models.appointment import AppointmentStatus

# Notação FDI: 2 dígitos numéricos.
# 1º dígito = quadrante (1-4 dentição permanente, 5-8 dentição decídua)
# 2º dígito = posição do dente no quadrante (1-8)
FDI_TOOTH_PATTERN = re.compile(r"^[1-8][1-8]$")


def validate_fdi_tooth(v: str | None) -> str | None:
    if v is None or v == "":
        return None
    if not FDI_TOOTH_PATTERN.match(v):
        raise ValueError(
            "Dente inválido. Use notação FDI: 2 dígitos numéricos, "
            "quadrante e posição de 1 a 8 (ex.: 11, 36)."
        )
    return v


class AppointmentProcedureCreate(BaseModel):
    procedure_id: int
    tooth: str | None = None

    @field_validator("tooth")
    @classmethod
    def validate_tooth(cls, v):
        return validate_fdi_tooth(v)


class AppointmentProcedureUpdate(BaseModel):
    """Payload para editar depois o dente (FDI) de um procedimento já
    lançado numa consulta. Enviar tooth=null (ou omitir) limpa o campo."""

    tooth: str | None = None

    @field_validator("tooth")
    @classmethod
    def validate_tooth(cls, v):
        return validate_fdi_tooth(v)


class AppointmentCreate(BaseModel):
    dentist_id: int
    patient_id: int

    procedures: list[AppointmentProcedureCreate]

    appointment_date: date
    time_begin: time
    time_end: time | None = None

    notes: str | None = None

    @field_validator("procedures")
    @classmethod
    def validate_procedures(cls, v):
        if not v:
            raise ValueError("Informe ao menos um procedimento")
        return v

    @field_validator("appointment_date")
    @classmethod
    def validate_not_in_past(cls, v):
        if v < date.today():
            raise ValueError("Não é possível agendar em uma data no passado")
        return v


class AppointmentUpdate(BaseModel):
    appointment_date: date | None = None
    time_begin: time | None = None
    time_end: time | None = None

    procedures: list[AppointmentProcedureCreate] | None = None

    notes: str | None = None

    @field_validator("procedures")
    @classmethod
    def validate_procedures(cls, v):
        if v is not None and not v:
            raise ValueError("Informe ao menos um procedimento")
        return v


class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus


class AppointmentNotesUpdate(BaseModel):
    """Payload exclusivo para editar a observação de uma consulta já
    existente, na página de Atendimento. Não usa AppointmentUpdate
    porque aquele schema é do fluxo de Agenda (permite mudar data,
    horário e procedimentos, e força o status de volta a AGENDADO)."""

    notes: str | None = None


class ProcedureSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    duration: int | None = None
    price: float


class AppointmentProcedureSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tooth: str | None = None
    procedure: ProcedureSummary


class AppointmentProcedureOut(BaseModel):
    """Resposta do PATCH /appointment-procedures/{id}."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    tooth: str | None = None
    display: str


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    clinic_id: str
    dentist_id: int
    patient_id: int

    procedures: list[AppointmentProcedureSummary]

    appointment_date: date
    time_begin: time
    time_end: time

    status: AppointmentStatus
    confirmation_message_sent: bool

    notes: str | None = None


class AppointmentResponseCard(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dentist_id: int
    patient_id: int

    procedures: list[str] = []

    appointment_date: date
    time_begin: time
    time_end: time

    status: AppointmentStatus
    confirmation_message_sent: bool

    @field_validator("procedures", mode="before")
    @classmethod
    def extract_procedure_names(cls, v):
        if not v:
            return []

        return [item.procedure.name for item in v]

class TableDataLine(BaseModel):
    id: int
    pacient_name: str
    dentist_name: str
    time_day: str
    procedures: list[str] = []
    total_price: float
    status: AppointmentStatus
    confirmation_message_sent: bool


class TableDetailProcedure(BaseModel):
    """Item de procedimento dentro do TableDetail. O `id` aqui é o id
    de AppointmentProcedure -- é ele que o PATCH
    /appointments/procedures/{id}/tooth espera para editar o dente."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    tooth: str | None = None
    price: float


class TableDetail(BaseModel):
    id: int
    pacient_name: str
    dentist_name: str
    time_day: str
    procedures: list[TableDetailProcedure]
    total_price: float
    duration: int
    status: AppointmentStatus
    confirmation_message_sent: bool
    notes: str | None = None

class TableDataLinePaginatedResponse(BaseModel):
    items: list[TableDataLine]
    page: int
    page_size: int
    total: int
    total_pages: int
    statistics: dict[str, float | int]

    class Config:
        from_attributes = True