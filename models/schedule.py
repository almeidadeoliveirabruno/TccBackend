from sqlalchemy import Column, Integer, String, Time, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from db.database import Base

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    time_begin =  Column(Time, nullable=False)
    time_end =  Column(Time, nullable=False)

    dentist_schedules = relationship(
        "DentistSchedule",
        back_populates="schedule",
        cascade="all, delete-orphan"
    )

    #table args serve para criar uma constraint de unicidade no banco de dados, garantindo que não haja horários duplicados
    __table_args__ = (
        UniqueConstraint("time_begin", "time_end", name="uq_horario_intervalo"),
    )
