from enum import Enum


class ProcedureCategory(str, Enum):
    PREVENTIVO = "Preventivo"
    RESTAURADOR = "Restaurador"
    CIRURGICO = "Cirúrgico"
    ESTETICO = "Estético"
    ORTODONTICO = "Ortodôntico"
    PROTESE = "Prótese"
    ENDODONTIA = "Endodontia"
    OUTRO = "Outro"