from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from models.dentist import Dentist
from models.schedule import Schedule
from models.associations.dentist_schedules import DentistSchedule
from schemas import dentist_schedule as schemas


def get_dentist_or_404(db: Session, dentist_id: int, clinic_id: str) -> Dentist:
    '''Garante que o dentista pertence à clínica solicitante, caso contrário retorna 404.'''
    dentist = (
        db.query(Dentist)
        .filter(
            Dentist.id == dentist_id,
            Dentist.clinic_id == clinic_id,
        )
        .first()
    )
    if not dentist:
        raise HTTPException(status_code=404, detail="Dentist not found.")
    return dentist


def get_dentist_schedule_or_404(
    db: Session, dentist_schedule_id: int, dentist_id: int, clinic_id: str
) -> DentistSchedule:
    """Garante que a associação de horário do dentista pertence à clínica solicitante, caso contrário retorna 404."""
    association = (
        db.query(DentistSchedule)
        .join(Dentist, DentistSchedule.dentist_id == Dentist.id)
        .filter(
            DentistSchedule.id == dentist_schedule_id,
            DentistSchedule.dentist_id == dentist_id,
            Dentist.clinic_id == clinic_id,
        )
        .first()
    )
    if not association:
        raise HTTPException(status_code=404, detail="Schedule entry not found.")
    return association


def get_or_create_schedule(db: Session, time_begin, time_end) -> Schedule:
    """Busca um horário existente ou cria um novo se não existir. Garante que não haja horários duplicados no banco de dados."""
    schedule = (
        db.query(Schedule)
        .filter(
            Schedule.time_begin == time_begin,
            Schedule.time_end == time_end,
        )
        .first()
    )

    if not schedule:
        schedule = Schedule(time_begin=time_begin, time_end=time_end)
        db.add(schedule)
        db.flush()  # get schedule.id without committing yet

    return schedule


def association_exists(
    db: Session, dentist_id: int, schedule_id: int, day_of_week: int, exclude_id: int | None = None
) -> bool:
    '''A função association_exists verifica se já existe uma associação de horário para um dentista específico em um determinado dia da semana. Se exclude_id for fornecido, a função ignora essa associação específica na verificação, permitindo atualizações sem conflito.'''
    query = db.query(DentistSchedule).filter(
        DentistSchedule.dentist_id == dentist_id,
        DentistSchedule.schedule_id == schedule_id,
        DentistSchedule.day_of_week == day_of_week,
    )
    if exclude_id is not None:
        query = query.filter(DentistSchedule.id != exclude_id)
    return query.first() is not None


# ---------- Create ----------

def create_dentist_schedules(
    db: Session,
    dentist_id: int,
    clinic_id: str,
    availability: list[schemas.ScheduleItem],
) -> schemas.AvailabilityResponse:
    get_dentist_or_404(db, dentist_id, clinic_id)

    if not availability:
        raise HTTPException(status_code=400, detail="At least one schedule must be provided.")

    schedules_created = []

    try:
        for item in availability:
            schedule = get_or_create_schedule(db, item.time_begin, item.time_end)

            if association_exists(db, dentist_id, schedule.id, item.day_of_week):
                continue  # already registered, skip

            new_association = DentistSchedule(
                dentist_id=dentist_id,
                schedule_id=schedule.id,
                day_of_week=item.day_of_week,
            )
            db.add(new_association)
            db.flush()

            schedules_created.append(
                schemas.ScheduleCreatedResponse(
                    id=new_association.id,
                    day_of_week=item.day_of_week,
                    time_begin=item.time_begin,
                    time_end=item.time_end,
                )
            )

    except IntegrityError:
        raise HTTPException(
            status_code=400,
            detail="Erro de integridade, possivelmente um horário duplicado.",
        )

    return schemas.AvailabilityResponse(
        dentist_id=dentist_id,
        schedules_created=schedules_created,
    )


# ---------- List ----------

def list_dentist_schedules(
    db: Session, dentist_id: int, clinic_id: str
) -> list[schemas.ScheduleCreatedResponse]:
    get_dentist_or_404(db, dentist_id, clinic_id)

    associations = (
        db.query(DentistSchedule)
        .join(Schedule, DentistSchedule.schedule_id == Schedule.id)
        .filter(DentistSchedule.dentist_id == dentist_id)
        .all()
    )

    return [
        schemas.ScheduleCreatedResponse(
            id=a.id,
            day_of_week=a.day_of_week,
            time_begin=a.schedule.time_begin,
            time_end=a.schedule.time_end,
        )
        for a in associations
    ]


# ---------- Update ----------

def update_dentist_schedule(
    db: Session,
    dentist_id: int,
    dentist_schedule_id: int,
    clinic_id: str,
    data: schemas.ScheduleUpdate,
) -> schemas.ScheduleCreatedResponse:
    get_dentist_or_404(db, dentist_id, clinic_id)
    association = get_dentist_schedule_or_404(db, dentist_schedule_id, dentist_id, clinic_id)

    schedule = get_or_create_schedule(db, data.time_begin, data.time_end)

    if association_exists(
        db, dentist_id, schedule.id, data.day_of_week, exclude_id=association.id
    ):
        raise HTTPException(
            status_code=400,
            detail="This dentist already has this schedule on the selected day.",
        )

    try:
        association.schedule_id = schedule.id
        association.day_of_week = data.day_of_week
        db.flush()
    except IntegrityError:
        raise HTTPException(
            status_code=400,
            detail="Integrity error while updating schedule.",
        )

    return schemas.ScheduleCreatedResponse(
        id=association.id,
        day_of_week=association.day_of_week,
        time_begin=data.time_begin,
        time_end=data.time_end,
    )


# ---------- Delete ----------

def delete_dentist_schedule(
    db: Session, dentist_id: int, dentist_schedule_id: int, clinic_id: str
) -> None:
    get_dentist_or_404(db, dentist_id, clinic_id)
    association = get_dentist_schedule_or_404(db, dentist_schedule_id, dentist_id, clinic_id)

    db.delete(association)
    db.flush()