from sqlalchemy import Column, Integer, ForeignKey,  UniqueConstraint
from sqlalchemy.orm import relationship
from db.database import Base


class DentistSchedule(Base):
    __tablename__ = "dentist_schedule"

    id = Column(Integer, primary_key=True, index=True)
    dentist_id = Column(Integer, ForeignKey("dentists.id"), nullable=False)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0 = domingo ... 6 = sábado

    dentist = relationship("Dentist", back_populates="schedules")
    schedule = relationship("Schedule", back_populates="dentist_schedules")

# A tabela args tem como objetivo criar uma constraint de unicidade no banco de dados, garantindo que não haja horários duplicados para o mesmo dentista em um mesmo dia da semana
    __table_args__ = (
        UniqueConstraint(
            "dentist_id", "schedule_id", "day_of_week",
            name="uq_dentist_schedule_day"
        ),
    )