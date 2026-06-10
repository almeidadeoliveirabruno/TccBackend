from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base

class Dentist(Base):
    __tablename__ = "dentists"

    id = Column(Integer, primary_key=True, index=True)

    nome = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    telefone = Column(String, nullable=False)
    cpf = Column(String, unique=True, nullable=False)

    cro = Column(String, unique=True, nullable=False)
    especialidade = Column(String, nullable=False)

    endereco_id = Column(Integer, ForeignKey("enderecos.id"))

    endereco = relationship("Endereco", back_populates="dentists")