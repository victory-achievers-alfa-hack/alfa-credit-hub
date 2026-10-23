from decimal import Decimal

from pydantic import Field
from .base import ApiSchema
from .enums import CreditGoal


class CreditProductResponse(ApiSchema):
    id: str = Field(..., examples=["working"])
    name: str = Field(..., examples=["Оборотный кредит"], max_length=127)
    short: str = Field(..., examples=["Для закупок, товара и текущих задач бизнеса"], max_length=255)
    goals: list[CreditGoal]
    min_amount: Decimal = Field(..., ge=0, examples=[100000])
    max_amount: Decimal = Field(..., ge=0, examples=[3000000])
    terms: list[int] = Field(..., examples=[[12, 24, 36]])
    rate: float = Field(..., description="Годовая ставка, %", examples=[24.0])


class CreditProductListResponse(ApiSchema):
    items: list[CreditProductResponse]
