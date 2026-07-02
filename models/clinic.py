import uuid

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from db.database import Base


class Clinic(Base):
    __tablename__ = "clinics"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    nome = Column(
        String,
        nullable=False
    )

    cnpj = Column(
        String,
        unique=True,
        nullable=False
    )

    users = relationship(
        "User",
        back_populates="clinic"
    )

    procedures = relationship(
        "Procedure",
        back_populates="clinic"
    )

    dentists = relationship(
        "Dentist",
        back_populates="clinic"
    )
