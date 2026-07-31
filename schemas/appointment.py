from datetime import date, time

from pydantic import BaseModel, ConfigDict, field_validator

from models.appointment import AppointmentStatus

class AppointmentProcedureCreate(BaseModel):
    procedure_id: int
    tooth: str | None = None
    @field_validator("tooth")
    @classmethod
    def validate_tooth(cls, v):
        if v is not None:
            if len(v) != 2 or not v.isdigit():
                raise ValueError(
                    "Dente deve estar no padrão FDI (ex: 11, 36)"
                )
        return v


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
    total_price: float
    status: AppointmentStatus
    confirmation_message_sent: bool

class TableDetail(BaseModel):
    id: int
    pacient_name: str
    dentist_name: str
    time_day: str
    tooths: str
    total_price: float
    duration: int
    status: AppointmentStatus
    confirmation_message_sent: bool
    notes: str

