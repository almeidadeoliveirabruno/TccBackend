from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True
    )

    email = Column(
        String,
        unique=True,
        nullable=False
    )

    hashed_password = Column(
        String,
        nullable=False
    )

    nome = Column(
        String,
        nullable=False
    )

    clinic_id = Column(
        String(36),
        ForeignKey("clinics.id"),
        nullable=False
    )

    clinic = relationship(
        "Clinic",
        back_populates="users"
    )