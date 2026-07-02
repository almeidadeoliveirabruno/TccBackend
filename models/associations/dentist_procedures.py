from sqlalchemy import Table, Column, Integer, ForeignKey
from db.database import Base

dentist_procedures = Table(
    "dentist_procedures",
    Base.metadata,
    Column("dentist_id", Integer, ForeignKey("dentists.id"), primary_key=True),
    Column("procedure_id", Integer, ForeignKey("procedures.id"), primary_key=True),
)