from pydantic import Field

from .base import ApiSchema, JsonDecimal
from .enums import CreditGoal


class CreditProductResponse(ApiSchema):
    id: str = Field(..., examples=["working"])
    name: str = Field(..., examples=["Оборотный кредит"], max_length=127)
    short_name: str = Field(..., max_length=127)
    description: str
    purposes: list[CreditGoal]
    min_amount: JsonDecimal = Field(..., ge=0, examples=[100000])
    max_amount: JsonDecimal = Field(..., ge=0, examples=[3000000])
    terms: list[int] = Field(..., examples=[[12, 24, 36]])
    rate: float = Field(..., description="Годовая ставка, %", examples=[24.0])
    accent: str


class CreditProductListResponse(ApiSchema):
    items: list[CreditProductResponse]
