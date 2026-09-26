from pydantic import BaseModel, ConfigDict
from typing import Optional


class AddressBase(BaseModel):
    street: str
    number: str
    complement: Optional[str] = None
    neighborhood: str
    city: str
    state: str
    cep: Optional[str] = None


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    street: Optional[str] = None
    number: Optional[str] = None
    complement: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    cep: Optional[str] = None


class AddressResponse(AddressBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
