from sqlalchemy import Table, Column, Integer, ForeignKey
from db.database import Base

dentist_specialties = Table(
    "dentist_specialties",
    Base.metadata,
    Column("dentist_id", Integer, ForeignKey("dentists.id"), primary_key=True),
    Column("specialty_id", Integer, ForeignKey("specialties.id"), primary_key=True),
)