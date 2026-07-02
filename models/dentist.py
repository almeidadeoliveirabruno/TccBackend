from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base
from models.associations.dentist_procedures import dentist_procedures

class Dentist(Base):
    __tablename__ = "dentists"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=False)
    cpf = Column(String, unique=True, nullable=False)
    cro = Column(String, unique=True, nullable=False)
    specialty = Column(String, nullable=True)

    clinic_id = Column(
        String(36),
        ForeignKey("clinics.id"),
        nullable=False
    )

    street = Column(String, nullable=False)
    number = Column(String, nullable=False)
    complement = Column(String, nullable=True)
    neighborhood = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    cep = Column(String, nullable=False)
    
    clinic = relationship("Clinic", back_populates="dentists")
    schedules = relationship("DentistSchedule", back_populates="dentist", cascade="all, delete-orphan")
    procedures = relationship("Procedure",secondary=dentist_procedures,back_populates="dentists")