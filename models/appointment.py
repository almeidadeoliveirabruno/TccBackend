import enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from db.database import Base


class AppointmentStatus(str, enum.Enum):
    AGENDADO = "agendado"
    CONFIRMADO = "confirmado"
    CANCELADO = "cancelado"
    REALIZADO = "realizado"
    FALTOU = "faltou"


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)

    clinic_id = Column(
        String(36),
        ForeignKey("clinics.id"),
        nullable=False,
        index=True,
    )

    dentist_id = Column(
        Integer,
        ForeignKey("dentists.id"),
        nullable=False,
        index=True,
    )

    patient_id = Column(
        Integer,
        ForeignKey("patients.id"),
        nullable=False,
        index=True,
    )

    appointment_date = Column(
        Date,
        nullable=False,
        index=True,
    )

    time_begin = Column(
        Time,
        nullable=False,
    )

    time_end = Column(
        Time,
        nullable=False,
    )

    status = Column(
        SqlEnum(AppointmentStatus, name="appointment_status"),
        nullable=False,
        default=AppointmentStatus.AGENDADO,
        server_default=AppointmentStatus.AGENDADO.value,
    )

    # Indica se a mensagem de confirmação via WhatsApp já foi enviada
    confirmation_message_sent = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    notes = Column(
        String,
        nullable=True,
    )

    clinic = relationship(
        "Clinic",
        back_populates="appointments",
    )

    dentist = relationship(
        "Dentist",
        back_populates="appointments",
    )

    patient = relationship(
        "Patient",
        back_populates="appointments",
    )

    procedure_items = relationship(
        "AppointmentProcedure",
        back_populates="appointment",
        cascade="all, delete-orphan",
    )

    @property
    def procedures(self):
        return self.procedure_items

    __table_args__ = (
        UniqueConstraint(
            "dentist_id",
            "appointment_date",
            "time_begin",
            name="uq_dentist_date_time_begin",
        ),
        CheckConstraint(
            "time_end > time_begin",
            name="ck_appointment_time_valid",
        ),
    )