from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from .catalog import CreditProductResponse
from .enums import CreditGoal


class RecommendationRequest(BaseModel):
    goal: CreditGoal
    amount: Decimal = Field(..., ge=50000, le=5000000, examples=[800000])
    term: int = Field(..., examples=[24])


class RecommendedOfferItem(BaseModel):
    product: CreditProductResponse
    calculation: FinanceCalculationSchema
    is_best_match: bool = False
    explanation: str = Field(..., examples=["При текущих показателях сумма не проходит проверку. Ориентир: до 150 000 ₽."])


class RecommendationResponse(BaseModel):
    items: list[RecommendedOfferItem]


class FinanceCalculationSchema(BaseModel):
    flow: Decimal = Field(..., description="Операционный остаток (выручка - расходы)")
    monthly_payment: Decimal = Field(..., ge=0, description="Ориентировочный платёж по новому кредиту")
    dscr: float = Field(..., description="Коэффициент покрытия (норма >= 1.25)")
    max_available_amount: Decimal = Field(..., description="Максимум по покрытию на этот срок")
    margin: float = Field(..., description="Рентабельность: (выручка - расходы) / выручка")
    score: int = Field(..., ge=0, le=100, description="Скоринговый балл из 100")
    eligible: bool = Field(..., description="Проходит ли предварительное правило автоматически")