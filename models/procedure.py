from sqlalchemy import Column, Integer, String, Float,  Boolean, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base

class Procedure(Base):
    __tablename__ = "procedures"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    category = Column(String, nullable=False)

    price = Column(Float, nullable=False)

    duration = Column(Integer, nullable=True)

    description = Column(String)

    status = Column(Boolean, default=True)

    clinic_id = Column(
        String(36),
        ForeignKey("clinics.id"),
        nullable=False
    )

    clinic = relationship(
        "Clinic",
        back_populates="procedures"
    )

