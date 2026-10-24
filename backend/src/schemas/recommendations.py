from decimal import Decimal

from pydantic import Field

from .base import ApiSchema, JsonDecimal
from .catalog import CreditProductResponse
from .enums import CreditGoal


class RecommendationRequest(ApiSchema):
    purpose: CreditGoal
    amount: Decimal = Field(..., ge=50000, le=5000000, examples=[800000])
    term_months: int = Field(..., gt=0, examples=[24])


class RecommendedOfferItem(ApiSchema):
    product: CreditProductResponse
    monthly_payment: JsonDecimal = Field(..., ge=0)
    coverage: JsonDecimal
    eligible: bool
    reason: str
    warning: str | None = None
    recommended_amount: JsonDecimal | None = Field(None, ge=0)


class RecommendationResponse(ApiSchema):
    items: list[RecommendedOfferItem]
