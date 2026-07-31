from decimal import Decimal
from pydantic import BaseModel, Field, field_serializer
from enums.ProcedureCategory import ProcedureCategory


class ProcedureCreate(BaseModel):
    name: str
    category: ProcedureCategory
    price: Decimal = Field(max_digits=10, decimal_places=2)
    duration: int | None = None
    description: str | None = None


class ProcedureUpdate(BaseModel):
    name: str | None = None
    category: ProcedureCategory | None = None
    price: Decimal | None = Field(default=None, max_digits=10, decimal_places=2)
    duration: int | None = None
    description: str | None = None


class ProcedureResponse(BaseModel):
    id: int
    name: str
    category: ProcedureCategory
    price: Decimal
    duration: int | None
    description: str | None

    class Config:
        from_attributes = True

    @field_serializer("price")
    def serialize_price(self, value: Decimal) -> float:
        return float(value)


class ProcedurePaginatedResponse(BaseModel):
    items: list[ProcedureResponse]
    page: int
    page_size: int
    total: int
    total_pages: int
    statistics: dict[str, float | int]

    class Config:
        from_attributes = True