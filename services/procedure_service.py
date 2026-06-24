from sqlalchemy.orm import Session
from models.procedure import Procedure
from schemas.procedure import ProcedureCreate, ProcedureResponse, ProcedureUpdate
from fastapi import HTTPException


# Função para criar um procedimento, associando-o à clínica do usuário autenticado
#verificar se o procedimento já existe para a clínica antes de criar um novo procedimento
def create_procedure(
    db: Session,
    procedure_create: ProcedureCreate,
    clinic_id: int
): 
    # Verificar se o procedimento já existe para a clínica
    existing_procedure = db.query(Procedure).filter(
        Procedure.name == procedure_create.name.title(),
        Procedure.clinic_id == clinic_id
    ).first()

    if existing_procedure:
        raise HTTPException(
            status_code=409,  
            detail="Já existe um procedimento com esse nome para esta clínica"
        )

    procedure = Procedure(
        name=procedure_create.name.title(),
        description=procedure_create.description,
        category=procedure_create.category,
        price=procedure_create.price,
        duration=procedure_create.duration,
        clinic_id=clinic_id
    )

    db.add(procedure)
    db.flush()

    return procedure

#Função para listar os procedimentos de uma clínica, usando o clinic_id do token de autenticação 
def get_procedures_by_clinic_id(
    db: Session,
    clinic_id: int
):
    return db.query(Procedure).filter(
        Procedure.clinic_id == clinic_id
    ).all()

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
    procedure = get_procedure_by_id(
        db,
        procedure_id,
        clinic_id
    )

    if not procedure:
        raise HTTPException(
            status_code=404,
            detail="Procedimento não encontrado"
        )

    if procedure.clinic_id != clinic_id:
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para atualizar este procedimento"
        )

# O método model_dump do Pydantic é usado para converter o objeto de atualização em um dicionário, excluindo os campos que não foram definidos (exclude_unset=True). Em seguida, o código itera sobre os itens do dicionário e usa setattr para atualizar os atributos do procedimento com os novos valores fornecidos.
    data = procedure_update.model_dump(exclude_unset=True)

    for key, value in data.items():
        setattr(procedure, key, value)

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