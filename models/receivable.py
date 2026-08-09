from datetime import datetime

from sqlalchemy import (
    Boolean,
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

class Receivable(Base):
    """
    Conta a receber. Um registro por consulta (appointment).
    Se o pagamento for parcelado, o detalhamento fica em `installments`;
    o `total_amount` e `status` aqui sempre refletem o total da consulta.
    """
 
    __tablename__ = "receivables"
 
    id = Column(Integer, primary_key=True, autoincrement=True)
 
   
    appointment_id = Column(
        Integer, ForeignKey("appointments.id"), nullable=False, unique=True, index=True
    )
 
    clinic_id = Column(String(36), ForeignKey("clinics.id"), nullable=False, index=True)
 
    total_amount = Column(Numeric(10, 2), nullable=False)
 
    # 'pendente' | 'parcial' | 'pago' | 'cancelado'
    status = Column(String(10), nullable=False, default="pendente")
 
    due_date = Column(Date, nullable=True)
    paid_at = Column(DateTime, nullable=True)
 
    # Preenchido só quando NÃO houver parcelamento (pagamento único)
    payment_method = Column(String(20), nullable=True)  # dinheiro, pix, cartao, etc.
 
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
 
    appointment = relationship("Appointment", backref="receivable", uselist=False)
    clinic = relationship("Clinic")
    installments = relationship(
        "Installment", back_populates="receivable", cascade="all, delete-orphan"
    )
 
    __table_args__ = (
        CheckConstraint(
            "status IN ('pendente','parcial','pago','cancelado')",
            name="ck_receivable_status",
        ),
    )
 
    @property
    def is_paid(self) -> bool:
        return self.status == "pago"
 