# from datetime import datetime
 
# from sqlalchemy import (
#     Column,
#     Integer,
#     String,
#     Numeric,
#     Date,
#     DateTime,
#     ForeignKey,
#     UniqueConstraint,
#     CheckConstraint,
# )
# from sqlalchemy.orm import relationship
 
# from db.database import Base

# class Installment(Base):
#     """
#     Parcela de uma conta a receber. Se a consulta não for parcelada,
#     simplesmente não existem linhas aqui para aquele receivable_id.
#     """
 
#     __tablename__ = "installments"
 
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     receivable_id = Column(
#         Integer, ForeignKey("receivables.id"), nullable=False, index=True
#     )
 
#     number = Column(Integer, nullable=False)  # 1, 2, 3...
#     amount = Column(Numeric(10, 2), nullable=False)
 
#     due_date = Column(Date, nullable=False)
#     paid_at = Column(DateTime, nullable=True)
 
#     # 'pendente' | 'pago' | 'atrasado' | 'cancelado'
#     status = Column(String(10), nullable=False, default="pendente")
#     payment_method = Column(String(20), nullable=True)
 
#     receivable = relationship("Receivable", back_populates="installments")
 
#     __table_args__ = (
#         UniqueConstraint("receivable_id", "number", name="uq_installment_number"),
#         CheckConstraint(
#             "status IN ('pendente','pago','atrasado','cancelado')",
#             name="ck_installment_status",
#         ),
#     )