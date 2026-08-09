from datetime import datetime
import enum 

from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    DateTime,
    Text,
    CheckConstraint
)
from sqlalchemy.orm import relationship

from db.database import Base


class ExpenseCategory(str, enum.Enum):
 
    ALUGUEL = "aluguel"                      # aluguel do consultório/sala
    CONTAS_FIXAS = "contas_fixas"            # água, luz, internet, telefone
    MATERIAL_ODONTOLOGICO = "material_odontologico"  # luvas, resina, anestésico, etc.
    EQUIPAMENTO = "equipamento"              # compra/manutenção de equipamento (autoclave, cadeira, raio-x)
    LABORATORIO = "laboratorio"              # laboratório de prótese
    SALARIO = "salario"                      # folha de pagamento (dentistas, recepção, etc.)
    PRO_LABORE = "pro_labore"                # retirada dos sócios
    MARKETING = "marketing"                  # anúncios, redes sociais, panfletos
    SOFTWARE = "software"                    # sistemas, assinaturas, licenças
    CONTABILIDADE = "contabilidade"          # honorários contábeis
    IMPOSTOS = "impostos"                    # tributos, taxas, alvarás
    LIMPEZA = "limpeza"                      # material e serviço de limpeza
    MANUTENCAO = "manutencao"                # reparos gerais do espaço
    OUTROS = "outros"

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    clinic_id = Column(String(36), ForeignKey("clinics.id"), nullable=False, index=True)
    description = Column(String(255), nullable=False)  # Campo para falar o que é a despesa
    category = Column(String(50), nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    due_date = Column(Date, nullable=False)
    paid_at = Column(DateTime, nullable=True)
    status = Column(String(10), nullable=False, default="pendente")
    notes = Column(Text, nullable=True)  # Campo para detalhar se necessário.
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    clinic = relationship("Clinic")
 
    __table_args__ = (
        CheckConstraint(
            "status IN ('pendente','pago','cancelado')", name="ck_expense_status"
        ),
    )