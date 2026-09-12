from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.clinic import Clinic
from schemas.clinic import ClinicCreate


def get_clinic_by_cnpj(
    db: Session,
    cnpj: str
):
    return db.query(Clinic).filter(
        Clinic.cnpj == cnpj
    ).first()


def _normalizar_cnpj(cnpj: str) -> str:
    """Remove tudo que não for dígito (pontos, barra, hífen, espaços)."""
    if cnpj is None:
        return ""

    cnpj_limpo = ""
    for caractere in cnpj:
        if caractere.isdigit():
            cnpj_limpo = cnpj_limpo + caractere

    return cnpj_limpo


def calcular_digito(cnpj_parcial: str, pesos: list[int]) -> int:
    """
    Calcula um dígito verificador do CNPJ.

    cnpj_parcial: string com os dígitos que serão usados no cálculo
                  (12 dígitos para o 1º verificador, 13 para o 2º)
    pesos: lista de multiplicadores oficiais, na mesma ordem dos dígitos
    """

    # Passo 1: multiplicar cada dígito pelo seu peso correspondente
    # e somar todos os resultados.
    soma = 0
    for i in range(len(cnpj_parcial)):
        digito = int(cnpj_parcial[i])
        peso = pesos[i]
        soma = soma + (digito * peso)

    # Passo 2: dividir a soma total por 11 e pegar o resto da divisão.
    resto = soma % 11

    # Passo 3: aplicar a regra oficial da Receita Federal:
    # - se o resto for 0 ou 1, o dígito verificador é 0
    # - caso contrário, o dígito é (11 - resto)
    if resto < 2:
        digito_verificador = 0
    else:
        digito_verificador = 11 - resto

    return digito_verificador


def _validar_cnpj(cnpj: str) -> str:
    """Valida formato básico e dígitos verificadores do CNPJ."""
    cnpj = _normalizar_cnpj(cnpj)

    if len(cnpj) != 14:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="CNPJ deve conter 14 dígitos"
        )

    if cnpj == "00000000000000":
        # obs: 0
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="CNPJ inválido"
        )

    # Pesos oficiais usados no cálculo do 1º dígito verificador.
    # Cada posição do CNPJ tem um peso fixo pelo qual seu dígito é multiplicado.
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    # Pesos oficiais usados no cálculo do 2º dígito verificador.
    # Repare que tem 13 pesos, pois o 2º dígito considera também o 1º
    # dígito verificador já calculado.
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    # Os 12 primeiros dígitos do CNPJ são a "base" da empresa.
    base_cnpj = cnpj[0:12]

    # Calcula o 1º dígito verificador usando apenas a base (12 dígitos).
    digito_1 = calcular_digito(base_cnpj, pesos1)

    # Para calcular o 2º dígito verificador, usa a base + o 1º dígito
    # que acabou de ser calculado (totalizando 13 dígitos).
    base_com_digito_1 = base_cnpj + str(digito_1)
    digito_2 = calcular_digito(base_com_digito_1, pesos2)

    # Monta os dois dígitos calculados como uma string, para comparar
    # com os 2 últimos dígitos informados no CNPJ original.
    digitos_calculados = str(digito_1) + str(digito_2)
    digitos_informados = cnpj[12:14]

    if digitos_informados != digitos_calculados:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="CNPJ inválido"
        )

    return cnpj


def create_clinic(
    db: Session,
    clinic_create: ClinicCreate
):
    nome = (clinic_create.nome or "").strip()
    if not nome:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nome da clínica é obrigatório"
        )

    cnpj = _validar_cnpj(clinic_create.cnpj)

    if get_clinic_by_cnpj(db, cnpj):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="CNPJ já cadastrado"
        )

    clinic = Clinic(
        nome=nome,
        cnpj=cnpj,
    )

    db.add(clinic)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Clínica já cadastrada"
        )

    return clinic