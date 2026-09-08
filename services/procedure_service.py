from sqlalchemy.orm import Session
from models.procedure import Procedure
from schemas.procedure import ProcedureCreate, ProcedureResponse, ProcedureUpdate
from fastapi import HTTPException
import math
from sqlalchemy import func

def _normalize_name(name: str) -> str:
    """Remove espaços em branco no início/fim, valida que não ficou vazio e aplica title case."""
    normalized = name.strip()

    if not normalized:
        raise HTTPException(
            status_code=400,
            detail="O nome do procedimento não pode ser vazio"
        )

    return normalized.title()

def _validate_price(price: float | None):
    """Valida se o preço do procedimento não é negativo."""
    if price is not None and price < 0:
        raise HTTPException(
            status_code=400,
            detail="O preço do procedimento não pode ser negativo"
        )

def _validate_unique_name(
    db: Session,
    name: str,
    clinic_id: int,
    exclude_procedure_id: int | None = None
):
    """Valida se já existe um procedimento com o mesmo nome na clínica."""
    query = db.query(Procedure).filter(
        Procedure.name == _normalize_name(name),
        Procedure.clinic_id == clinic_id
    )

    if exclude_procedure_id is not None:
        query = query.filter(Procedure.id != exclude_procedure_id)

    if query.first():
        raise HTTPException(
            status_code=409,
            detail="Já existe um procedimento com esse nome para esta clínica"
        )


def _validate_time_duration(duration: int | None):
    """Valida se a duração do procedimento não é negativa."""
    if duration is not None and duration < 0:
        raise HTTPException(
            status_code=400,
            detail="A duração do procedimento não pode ser negativa"
        )

# Função para criar um procedimento, associando-o à clínica do usuário autenticado
#verificar se o procedimento já existe para a clínica antes de criar um novo procedimento
def create_procedure(
    db: Session,
    procedure_create: ProcedureCreate,
    clinic_id: int
):
    _validate_unique_name(db, procedure_create.name, clinic_id)
    _validate_price(procedure_create.price)
    _validate_time_duration(procedure_create.duration)

    procedure = Procedure(
        name=_normalize_name(procedure_create.name),
        description=procedure_create.description,
        category=procedure_create.category,
        price=procedure_create.price,
        duration=procedure_create.duration,
        clinic_id=clinic_id
    )

    db.add(procedure)
    db.flush()

    return procedure

def get_procedures_by_clinic_id(
    db: Session,
    clinic_id: int,
    page: int = 1,
    page_size: int = 10,
    search: str | None = None,
    category: str | None = None,
):
    skip = (page - 1) * page_size

    query = db.query(Procedure).filter(Procedure.clinic_id == clinic_id)

    if search:
        like = f"%{search}%"
        query = query.filter(
            (Procedure.name.ilike(like)) | (Procedure.category.ilike(like))
        )

    if category:
        query = query.filter(Procedure.category == category)

    total = query.count()

    procedures = (
        query
        .order_by(Procedure.name)
        .offset(skip)
        .limit(page_size)
        .all()
    )

    statistics = statistics_procedures(db, clinic_id)  

    return {
        "items": procedures,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": max(1, math.ceil(total / page_size)) if total else 1,
        "statistics": statistics
    }

#Função para obter um procedimento específico por ID, garantindo que ele pertença à clínica do usuário autenticado
def get_procedure_by_id(
    db: Session,
    procedure_id: int,
    clinic_id: int
):
    procedure = db.query(Procedure).filter(
        Procedure.id == procedure_id,
        Procedure.clinic_id == clinic_id
    ).first()

    if not procedure:
        raise HTTPException(
            status_code=404,
            detail="Procedimento não encontrado"
        )
    return procedure

def update_procedure(
    db: Session,
    procedure_id: int,
    procedure_update: ProcedureUpdate,
    clinic_id: int
):
    procedure = get_procedure_by_id(db, procedure_id, clinic_id)

    if procedure.clinic_id != clinic_id:
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para atualizar este procedimento"
        )

    if procedure_update.name is not None:
        _validate_unique_name(
            db,
            procedure_update.name,
            clinic_id,
            exclude_procedure_id=procedure_id
        )

    if procedure_update.price is not None:
        _validate_price(procedure_update.price)

    if procedure_update.duration is not None:
        _validate_time_duration(procedure_update.duration)

    data = procedure_update.model_dump(exclude_unset=True)

    for key, value in data.items():
        if key == "name":
            value = _normalize_name(value)

        setattr(procedure, key, value)

    db.flush()
    db.refresh(procedure)

    return procedure

def delete_procedure(
    db: Session,
    procedure_id: int,
    clinic_id: int
):
    procedure = get_procedure_by_id(db, procedure_id, clinic_id)

    if not procedure:
        raise HTTPException(
            status_code=404,
            detail="Procedimento não encontrado"
        )

    if procedure.clinic_id != clinic_id:
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para deletar este procedimento"
        )
    db.delete(procedure)
    db.flush()

    return procedure

#função para pesquisar procedimentos por nome ou categoria, garantindo que eles pertençam à clínica do usuário autenticado
def search_procedures(
    db: Session,
    search_query: str,
    clinic_id: int
):
    #ilike é usado para realizar uma busca insensível a maiúsculas e minúsculas, permitindo que o usuário encontre procedimentos independentemente de como ele digita o nome ou a categoria.
    procedures = db.query(Procedure).filter(
        Procedure.clinic_id == clinic_id,
        (Procedure.name.ilike(f"%{search_query}%")) | (Procedure.category.ilike(f"%{search_query}%"))
    ).all()

    return procedures

def statistics_procedures(
    db: Session,
    clinic_id: int
):
    result = (
        db.query(
            func.count(Procedure.id).label("total_procedures"),
            func.avg(Procedure.price).label("average_price"),
            func.max(Procedure.price).label("max_price"),
            func.count(func.distinct(Procedure.category)).label("unique_categories"),
        )
        .filter(Procedure.clinic_id == clinic_id)
        .one()
    )

    return {
        "total_procedures": result.total_procedures,
        "average_price": float(result.average_price or 0),
        "max_price": float(result.max_price or 0),
        "unique_categories": result.unique_categories,
    }