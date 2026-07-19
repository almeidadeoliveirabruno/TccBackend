import math
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException

from models.dentist import Dentist, DentistStatus
from models.specialty import Specialty
from models.associations.dentist_specialties import dentist_specialties
from schemas.dentist import DentistCreate, DentistUpdate
from core.security import hash_cpf, encrypt_cpf


def get_or_create_specialty(db: Session, name: str) -> Specialty:
    """Busca uma especialidade existente (case-insensitive) ou cria uma nova.
    Mesmo padrao do get_or_create_schedule ja usado em dentist_schedule_service:
    checa antes, cria se nao achou, da flush pra conseguir o id sem commitar."""
    name = name.strip()
    specialty = (
        db.query(Specialty)
        .filter(func.lower(Specialty.name) == name.lower())
        .first()
    )
    if not specialty:
        specialty = Specialty(name=name)
        db.add(specialty)
        db.flush()
    return specialty


def _resolve_specialties(db: Session, names: list[str]) -> list[Specialty]:
    # dict.fromkeys em vez de set() pra manter a ordem em que foram digitadas
    #A função abaixo remove duplicatas e espaços em branco da lista de especialidades, mantendo a ordem original. Em seguida, ela chama get_or_create_specialty para cada especialidade única, garantindo que cada uma exista no banco de dados e retornando uma lista de objetos Specialty.
    unique_names = list(dict.fromkeys(n.strip() for n in names if n and n.strip()))
    return [get_or_create_specialty(db, name) for name in unique_names]


def create_dentist(
    db: Session,
    dentist_create: DentistCreate,
    clinic_id: str,
):
    cpf_hash = hash_cpf(dentist_create.cpf)

    existing_dentist = (
        db.query(Dentist)
        .filter(Dentist.cpf_hash == cpf_hash, Dentist.clinic_id == clinic_id)
        .first()
    )
    if existing_dentist:
        raise HTTPException(
            status_code=409,
            detail="Já existe um dentista com esse CPF cadastrado nesta clínica",
        )

    specialties = _resolve_specialties(db, dentist_create.specialties)

    dentist = Dentist(
        name=dentist_create.name.title(),
        cpf_hash=cpf_hash,
        cpf_encrypted=encrypt_cpf(dentist_create.cpf),
        email=dentist_create.email,
        phone=dentist_create.phone,
        clinic_id=clinic_id,
        cro=dentist_create.cro,
        specialties=specialties,
        street=dentist_create.street,
        number=dentist_create.number,
        complement=dentist_create.complement,
        neighborhood=dentist_create.neighborhood,
        city=dentist_create.city,
        state=dentist_create.state,
        cep=dentist_create.cep,
        status=dentist_create.status,
    )

    db.add(dentist)
    db.flush()

    # Nota: criacao de `schedules` na mesma chamada nao esta feita aqui de
    # proposito — o service de dentist_schedule ja existe e valida tudo
    # certinho (get_or_create_schedule, association_exists, etc). Melhor
    # a rota chamar create_dentist_schedules() logo em seguida, dentro da
    # mesma transacao, do que duplicar essa logica aqui.

    return dentist


def get_dentist_by_id(db: Session, dentist_id: int, clinic_id: str) -> Dentist:
    dentist = (
        db.query(Dentist)
        .filter(Dentist.id == dentist_id, Dentist.clinic_id == clinic_id)
        .first()
    )
    if not dentist:
        raise HTTPException(status_code=404, detail="Dentista não encontrado")
    return dentist


def get_dentists_by_clinic_id(
    db: Session,
    clinic_id: str,
    page: int = 1,
    page_size: int = 10,
    search: str | None = None,
    specialty: str | None = None,
    status: DentistStatus | None = None,
):
    skip = (page - 1) * page_size

    query = db.query(Dentist).filter(Dentist.clinic_id == clinic_id)

    if search:
        like = f"%{search}%"
        query = query.filter((Dentist.name.ilike(like)) | (Dentist.cro.ilike(like)))

    if specialty:
        query = query.filter(Dentist.specialties.any(Specialty.name == specialty))

    if status:
        query = query.filter(Dentist.status == status)

    total = query.count()

    dentists = query.order_by(Dentist.name).offset(skip).limit(page_size).all()

    statistics = statistics_dentists(db, clinic_id)

    return {
        "items": dentists,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": max(1, math.ceil(total / page_size)) if total else 1,
        "statistics": statistics,
    }


def update_dentist(
    db: Session,
    dentist_id: int,
    dentist_update: DentistUpdate,
    clinic_id: str,
):
    dentist = get_dentist_by_id(db, dentist_id, clinic_id)

    data = dentist_update.model_dump(exclude_unset=True, exclude={"specialties"})
    for key, value in data.items():
        setattr(dentist, key, value)

    if dentist_update.specialties is not None:
        dentist.specialties = _resolve_specialties(db, dentist_update.specialties)

    db.flush()
    return dentist


def update_dentist_status(
    db: Session,
    dentist_id: int,
    status: DentistStatus,
    clinic_id: str,
):
    """Troca só o status do dentista — usado pela rota PATCH /dentists/{id}/status,
    pra não precisar mandar o objeto inteiro só pra marcar férias/inativo/etc."""
    dentist = get_dentist_by_id(db, dentist_id, clinic_id)
    dentist.status = status
    db.flush()
    return dentist


def delete_dentist(db: Session, dentist_id: int, clinic_id: str):
    dentist = get_dentist_by_id(db, dentist_id, clinic_id)
    db.delete(dentist)
    db.flush()
    return dentist


def search_dentists(db: Session, search_query: str, clinic_id: str):
    return (
        db.query(Dentist)
        .filter(
            Dentist.clinic_id == clinic_id,
            (Dentist.name.ilike(f"%{search_query}%"))
            | (Dentist.cro.ilike(f"%{search_query}%")),
        )
        .all()
    )


def get_distinct_specialties(db: Session, clinic_id: str) -> list[str]:
    """Lista as especialidades ja usadas por algum dentista da clinica,
    pra alimentar sugestao/autocomplete no frontend."""
    rows = (
        db.query(Specialty.name)
        .join(dentist_specialties, Specialty.id == dentist_specialties.c.specialty_id)
        .join(Dentist, Dentist.id == dentist_specialties.c.dentist_id)
        .filter(Dentist.clinic_id == clinic_id)
        .distinct()
        .order_by(Specialty.name)
        .all()
    )
    return [r[0] for r in rows]


def statistics_dentists(db: Session, clinic_id: str):
    total_dentists = (
        db.query(func.count(Dentist.id))
        .filter(Dentist.clinic_id == clinic_id)
        .scalar()
    )

    unique_specialties = (
        db.query(func.count(func.distinct(Specialty.id)))
        .join(dentist_specialties, Specialty.id == dentist_specialties.c.specialty_id)
        .join(Dentist, Dentist.id == dentist_specialties.c.dentist_id)
        .filter(Dentist.clinic_id == clinic_id)
        .scalar()
    ) or 0

    status_counts_query = (
        db.query(Dentist.status, func.count(Dentist.id))
        .filter(Dentist.clinic_id == clinic_id)
        .group_by(Dentist.status)
        .all()
    )
    by_status = {s.value: 0 for s in DentistStatus}
    for status, count in status_counts_query:
        by_status[status.value if hasattr(status, "value") else status] = count

    return {
        "total_dentists": total_dentists,
        "unique_specialties": unique_specialties,
        "by_status": by_status,
    }