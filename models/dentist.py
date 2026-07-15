import enum
from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SqlEnum
from sqlalchemy.orm import relationship
from db.database import Base
from models.associations.dentist_specialties import dentist_specialties


class DentistStatus(str, enum.Enum):
    ATIVO = "ativo"
    INATIVO = "inativo"
    FERIAS = "ferias"
    AFASTADO = "afastado"


class Dentist(Base):
    __tablename__ = "dentists"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=False)

    # cpf_hash: deterministico, usado so para checar duplicidade/busca exata.
    # cpf_encrypted: reversivel (Fernet), guarda o valor real criptografado.
    cpf_hash = Column(String(64), unique=True, nullable=False, index=True)
    cpf_encrypted = Column(String, nullable=False)

    cro = Column(String, unique=True, nullable=False)

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
    cep = Column(String, nullable=False)

    clinic = relationship("Clinic", back_populates="dentists")
    schedules = relationship("DentistSchedule", back_populates="dentist", cascade="all, delete-orphan")
    specialties = relationship("Specialty", secondary=dentist_specialties, back_populates="dentists")

    @property
    def cpf(self) -> str:
        """CPF descriptografado sob demanda - nao fica em memoria alem do uso pontual."""
        from core.security import decrypt_cpf
        return decrypt_cpf(self.cpf_encrypted)

    @property
    def cpf_masked(self) -> str:
        """Versao mascarada, pra usar em listagens (evita expor o CPF completo a toa)."""
        from core.security import mask_cpf
        return mask_cpf(self.cpf)