from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from db.database import Base
from models.associations.dentist_specialties import dentist_specialties


class Specialty(Base):
    __tablename__ = "specialties"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, unique=True, nullable=False, index=True)

    dentists = relationship("Dentist", secondary=dentist_specialties, back_populates="specialties")