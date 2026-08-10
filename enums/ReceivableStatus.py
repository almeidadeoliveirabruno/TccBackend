from enum import Enum

class ReceivableStatus(str, Enum):
    PENDENTE = "pendente"
    PARCIAL = "parcial"
    PAGO = "pago"
    CANCELADO = "cancelado"