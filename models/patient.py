from sqlalchemy import Column, Integer, String,ForeignKey
from db.database import Base
from sqlalchemy.orm import relationship

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)

    nome = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    telefone = Column(String, nullable=False)
    cpf = Column(String, unique=True, nullable=False)

    data_nascimento = Column(String, nullable=False)
    sexo = Column(String, nullable=False)

    endereco_id = Column(Integer, ForeignKey("enderecos.id"))

    endereco = relationship("Endereco", back_populates="patients")