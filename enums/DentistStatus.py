from enum import Enum

class DentistStatus(str, Enum):
    ATIVO = "Ativo"
    INATIVO = "Inativo"
    FERIAS = "Ferias"
    AFASTADO = "Afastado"