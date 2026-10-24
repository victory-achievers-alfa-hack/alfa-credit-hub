"""Typed API contracts; business rules live in scoring/."""

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator

Purpose = Literal["goods", "equipment", "cash_gap"]
Preference = Literal["min_interest", "min_payment"]
Money = Annotated[float, Field(ge=0, allow_inf_nan=False)]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RecommendationRequest(Contract):
    companyId: Annotated[str, Field(min_length=1, max_length=128)] | None = None
    purpose: Purpose
    amount: Annotated[
        Decimal, Field(gt=0, le=10**12, decimal_places=2, allow_inf_nan=False)
    ]
    termMonths: Annotated[int, Field(strict=True, ge=1, le=120)]
    preference: Preference = "min_interest"

    @field_validator("amount", mode="before")
    @classmethod
    def reject_boolean_amount(cls, value):
        if isinstance(value, bool):
            raise ValueError("amount must be numeric")
        return value


class Factor(Contract):
    code: str
    label: str
    value: str
    positive: bool
    points: Annotated[int, Field(ge=0)]
    maxPoints: Annotated[int, Field(gt=0)]


class Scoring(Contract):
    score: Annotated[int, Field(ge=0, le=100)]
    riskLevel: Literal["low", "medium", "high"]
    summary: str
    factors: list[Factor]
    modelVersion: str
    featureVersion: str
    calculatedAt: AwareDatetime
    eventProbability: None


class Offer(Contract):
    amount: Money
    termMonths: int
    rate: Money
    monthlyPayment: Money
    lastPayment: Money
    totalRepayment: Money
    interestAmount: Money
    coverage: Annotated[float, Field(allow_inf_nan=False)]
    eligible: bool


class Reason(Contract):
    code: str
    message: str


class Check(Contract):
    id: str
    label: str
    value: str
    description: str
    state: Literal["success", "warning", "error"]


class Evaluation(Offer):
    productId: str
    purpose: Purpose
    assessment: Literal[
        "eligible",
        "alternative",
        "need_info",
        "manual_review",
        "blocked",
        "unavailable",
    ]
    reasons: list[Reason]
    checks: list[Check]
    alternative: Offer | None
    recommendedAmount: Money | None
    scoring: Scoring
    policyVersion: str
    calculatedAt: AwareDatetime


class Product(Contract):
    id: str
    name: str
    minAmount: Money
    maxAmount: Money
    rate: Money
    terms: list[int]
    purposes: list[Purpose]
    shortName: str | None = None
    description: str | None = None
    accent: str | None = None


class RankedOffer(Contract):
    product: Product
    evaluation: Evaluation
    offer: Offer
    termChanged: bool
    amountShortfall: Money
    group: Literal[
        "requested", "other_terms", "reduced_amount", "requires_action", "unavailable"
    ]
    rankInGroup: Annotated[int, Field(ge=1)]
    rankingReason: str


class Groups(Contract):
    requested: list[RankedOffer]
    other_terms: list[RankedOffer]
    reduced_amount: list[RankedOffer]
    requires_action: list[RankedOffer]
    unavailable: list[RankedOffer]


class RecommendationResponse(Contract):
    evaluationId: str
    companyId: str
    rankingVersion: str
    preference: Preference
    requestedAmount: Money
    requestedTermMonths: int
    calculatedAt: AwareDatetime
    groups: Groups


class ErrorDetail(Contract):
    code: str
    message: str


class ErrorResponse(Contract):
    detail: ErrorDetail
