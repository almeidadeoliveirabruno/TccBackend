import enum
from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SqlEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from db.database import Base
from models.associations.dentist_specialties import dentist_specialties
from enums.DentistStatus import DentistStatus



class Dentist(Base):
    __tablename__ = "dentists"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String, nullable=False)

    # cpf_hash -> usado para comparação/deduplicação
    # cpf_encrypted -> valor real criptografado
    cpf_hash = Column(
        String(64),
        nullable=False,
        index=True
    )

    cpf_encrypted = Column(
        String,
        nullable=False
    )

    cro = Column(String(20), nullable=False)

    status = Column(
        SqlEnum(DentistStatus, name="dentist_status"),
        nullable=False,
        default=DentistStatus.ATIVO,
        server_default=DentistStatus.ATIVO.value,
    )

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
    cep = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "clinic_id",
            "cpf_hash",
            name="uq_dentist_cpf_clinic"
        ),
        UniqueConstraint(
            "clinic_id",
            "cro",
            name="uq_dentist_cro_clinic"
        ),
    )


    clinic = relationship(
        "Clinic",
        back_populates="dentists"
    )

    schedules = relationship(
        "DentistSchedule",
        back_populates="dentist",
        cascade="all, delete-orphan"
    )

    specialties = relationship(
        "Specialty",
        secondary=dentist_specialties,
        back_populates="dentists"
    )

    appointments = relationship(
        "Appointment",
        back_populates="dentist"
    )


    @property
    def cpf(self) -> str:
        """CPF descriptografado sob demanda."""
        from core.security import decrypt_cpf
        return decrypt_cpf(self.cpf_encrypted)


    @property
    def cpf_masked(self) -> str:
        """CPF mascarado para listagens."""
        from core.security import mask_cpf
        return mask_cpf(self.cpf)