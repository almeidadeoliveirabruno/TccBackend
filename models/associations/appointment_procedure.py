from sqlalchemy import Column, Integer, String, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from db.database import Base


class AppointmentProcedure(Base):

    __tablename__ = "appointment_procedures"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False, index=True)
    procedure_id = Column(Integer, ForeignKey("procedures.id"), nullable=False, index=True)
    tooth = Column(String(2), nullable=True)
    unit_price = Column(Numeric(10, 2),nullable=False)
    appointment = relationship("Appointment", back_populates="procedure_items")
    procedure = relationship("Procedure", back_populates="appointment_items")
   