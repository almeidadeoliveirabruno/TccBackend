from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db.dependencies import get_db, get_current_clinic_id
from schemas.procedure import (
    ProcedureCreate,
    ProcedureUpdate,
    ProcedureResponse,
    ProcedurePaginatedResponse,
)
from services.procedure_service import (
    create_procedure,
    get_procedures_by_clinic_id,
    get_procedure_by_id,
    update_procedure,
    delete_procedure,
    search_procedures
)

router = APIRouter(
    prefix="/procedures",
    tags=["Procedures"]
)


# Criar procedimento
@router.post("/", response_model=ProcedureResponse)
def create_procedure_endpoint(
    procedure_create: ProcedureCreate,
    db: Session = Depends(get_db),
    clinic_id: int = Depends(get_current_clinic_id)
):
    return create_procedure(db, procedure_create, clinic_id)


# Listar todos os procedimentos da clínica
@router.get("/", response_model=ProcedurePaginatedResponse)
def get_procedures(
    page: int = Query(1, ge=1),
    page_size: int = Query(3, ge=1, le=20),
    search: str | None = Query(None),
    category: str | None = Query(None),
    db: Session = Depends(get_db),
    clinic_id: int = Depends(get_current_clinic_id)
):
    return get_procedures_by_clinic_id(
        db=db,
        clinic_id=clinic_id,
        page=page,
        page_size=page_size,
        search = search,
        category = category
    )

#Buscar procedimento pelo nome
@router.get("/search", response_model=ProcedureResponse)
def get_procedures(
    search_query: str | None = None,
    db: Session = Depends(get_db),
    clinic_id: int = Depends(get_current_clinic_id)
):
    print(search_query)
    if search_query:
        return search_procedures(db, search_query, clinic_id)
    return get_procedures_by_clinic_id(db, clinic_id)

# Buscar procedimento pelo ID
@router.get("/{procedure_id}", response_model=ProcedureResponse)
def get_procedure(
    procedure_id: int,
    db: Session = Depends(get_db),
    clinic_id: int = Depends(get_current_clinic_id)
):
    procedure = get_procedure_by_id(db, procedure_id, clinic_id)

    return procedure


# Atualizar procedimento
@router.put("/{procedure_id}", response_model=ProcedureResponse)
def update_procedure_endpoint(
    procedure_id: int,
    procedure_update: ProcedureUpdate,
    db: Session = Depends(get_db),
    clinic_id: int = Depends(get_current_clinic_id)
):
    updated_procedure = update_procedure(
        db,
        procedure_id,
        procedure_update,
        clinic_id
    )

    return updated_procedure


# Deletar procedimento
@router.delete("/{procedure_id}")
def delete_procedure_endpoint(
    procedure_id: int,
    db: Session = Depends(get_db),
    clinic_id: int = Depends(get_current_clinic_id)
    ):
    delete_procedure(db, procedure_id, clinic_id)

    return {"detail": "Procedimento deletado com sucesso"}


