from enum import Enum

class DentistStatus(str, Enum):
    ATIVO = "Ativo"
    INATIVO = "Inativo"
    FERIAS = "Férias"
    AFASTADO = "Afastado"