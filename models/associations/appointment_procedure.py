from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base


class AppointmentProcedure(Base):
    """
    Association object entre Appointment e Procedure.

    Precisa ser um model próprio (com id próprio), e não uma Table simples
    tipo dentist_specialties, porque o MESMO procedimento pode se repetir
    na mesma consulta — ex.: restauração no dente 11 e restauração no
    dente 36. Uma Table com chave composta (appointment_id, procedure_id)
    não permitiria isso, já que o par se repetiria e violaria a PK.
    """

    __tablename__ = "appointment_procedures"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False, index=True)
    procedure_id = Column(Integer, ForeignKey("procedures.id"), nullable=False, index=True)

    # Dente afetado, notação FDI (ex.: "11", "36"). Nullable porque nem
    # todo procedimento é específico de um dente (ex.: limpeza geral).
    tooth = Column(String(2), nullable=True)

    appointment = relationship("Appointment", back_populates="procedure_items")
    procedure = relationship("Procedure", back_populates="appointment_items")