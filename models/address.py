from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from db.database import Base


class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    street = Column(String, nullable=False)
    number = Column(String, nullable=False)
    complement = Column(String, nullable=True)
    neighborhood = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    cep = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
