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
        raise HTTPException(status_code=404, detail="Dentista não encontrado.")
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
        raise HTTPException(status_code=404, detail="Entrada de horário não encontrada.")
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
    '''Verifica se já existe uma associação idêntica (mesmo dentista, mesmo horário exato, mesmo dia).'''
    query = db.query(DentistSchedule).filter(
        DentistSchedule.dentist_id == dentist_id,
        DentistSchedule.schedule_id == schedule_id,
        DentistSchedule.day_of_week == day_of_week,
    )
    if exclude_id is not None:
        query = query.filter(DentistSchedule.id != exclude_id)
    return query.first() is not None


def _ranges_overlap(begin_a, end_a, begin_b, end_b) -> bool:
    """Dois intervalos se sobrepõem se um começa antes do outro terminar
    e vice-versa. Limites que só se tocam (ex: 08:00-10:00 e 10:00-12:00)
    NÃO contam como sobreposição."""
    return begin_a < end_b and begin_b < end_a


def _assert_no_overlap(
    db: Session,
    dentist_id: int,
    day_of_week: int,
    time_begin,
    time_end,
    exclude_association_id: int | None = None,
    extra_ranges: list[tuple] | None = None,
) -> None:
    """Levanta 400 se o intervalo [time_begin, time_end) sobrepõe algum
    horário já cadastrado pro dentista nesse dia da semana. `extra_ranges`
    permite checar também contra itens ainda não persistidos (útil ao
    criar vários horários na mesma chamada)."""
    query = (
        db.query(DentistSchedule)
        .join(Schedule, DentistSchedule.schedule_id == Schedule.id)
        .filter(
            DentistSchedule.dentist_id == dentist_id,
            DentistSchedule.day_of_week == day_of_week,
        )
    )
    if exclude_association_id is not None:
        query = query.filter(DentistSchedule.id != exclude_association_id)

    for assoc in query.all():
        if _ranges_overlap(time_begin, time_end, assoc.schedule.time_begin, assoc.schedule.time_end):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Esse horário sobrepõe outro já cadastrado para este dentista "
                    f"no mesmo dia ({assoc.schedule.time_begin}–{assoc.schedule.time_end})."
                ),
            )

    for begin_x, end_x in extra_ranges or []:
        if _ranges_overlap(time_begin, time_end, begin_x, end_x):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Dois horários enviados na mesma requisição se sobrepõem "
                    f"no mesmo dia ({begin_x}–{end_x})."
                ),
            )


# ---------- Create ----------

def create_dentist_schedules(
    db: Session,
    dentist_id: int,
    clinic_id: str,
    availability: list[schemas.ScheduleItem],
) -> schemas.AvailabilityResponse:
    get_dentist_or_404(db, dentist_id, clinic_id)

    if not availability:
        raise HTTPException(status_code=400, detail="Pelo menos um horário deve ser fornecido.")

    schedules_created = []
    # Guarda os ranges já aceitos nesta mesma chamada, agrupados por dia,
    # pra pegar sobreposição entre itens do próprio payload.
    accepted_ranges_by_day: dict[int, list[tuple]] = {}

    try:
        for item in availability:
            _assert_no_overlap(
                db,
                dentist_id,
                item.day_of_week,
                item.time_begin,
                item.time_end,
                extra_ranges=accepted_ranges_by_day.get(item.day_of_week, []),
            )

            schedule = get_or_create_schedule(db, item.time_begin, item.time_end)

            if association_exists(db, dentist_id, schedule.id, item.day_of_week):
                continue  # já cadastrado exatamente igual, pula

            new_association = DentistSchedule(
                dentist_id=dentist_id,
                schedule_id=schedule.id,
                day_of_week=item.day_of_week,
            )
            db.add(new_association)
            db.flush()

            accepted_ranges_by_day.setdefault(item.day_of_week, []).append(
                (item.time_begin, item.time_end)
            )

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

    _assert_no_overlap(
        db,
        dentist_id,
        data.day_of_week,
        data.time_begin,
        data.time_end,
        exclude_association_id=association.id,
    )

    schedule = get_or_create_schedule(db, data.time_begin, data.time_end)

    if association_exists(
        db, dentist_id, schedule.id, data.day_of_week, exclude_id=association.id
    ):
        raise HTTPException(
            status_code=400,
            detail="Este dentista já possui este horário no dia selecionado.",
        )

    try:
        association.schedule_id = schedule.id
        association.day_of_week = data.day_of_week
        db.flush()
    except IntegrityError:
        raise HTTPException(
            status_code=400,
            detail="Erro de integridade ao atualizar horário.",
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