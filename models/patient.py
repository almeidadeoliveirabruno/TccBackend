from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from db.database import Base
from sqlalchemy.orm import relationship


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=False)

    cpf_hash = Column(
        String(64),
        nullable=False,
        index=True
    )

    cpf_encrypted = Column(
        String,
        nullable=False
    )

    birth_date = Column(String, nullable=False)
    gender = Column(String, nullable=False)

    observations = Column(String, nullable=True)
    health_plan = Column(String, nullable=True)
    profession = Column(String, nullable=False)

    street = Column(String, nullable=False)
    number = Column(String, nullable=False)
    complement = Column(String, nullable=True)
    neighborhood = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    cep = Column(String, nullable=True)

    clinic_id = Column(
        String(36),
        ForeignKey("clinics.id"),
        nullable=False
    )


    __table_args__ = (
        UniqueConstraint(
            "clinic_id",
            "cpf_hash",
            name="uq_patient_cpf_clinic"
        ),
    )


    clinic = relationship(
        "Clinic",
        back_populates="patients"
    )

    appointments = relationship(
        "Appointment",
        back_populates="patient"
    )