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
    reviewRequired: bool = False


class Reason(Contract):
    code: str
    message: str
    field: str | None = None
    actual: float | str | None = None
    minimum: float | None = None
    maximum: float | None = None
    allowedValues: list[int | str] | None = None


class Check(Contract):
    id: str
    label: str
    value: str
    description: str
    state: Literal["success", "warning", "error"]


class NextAction(Contract):
    code: str
    title: str
    message: str
    amount: Money | None = None
    termMonths: int | None = None
    documentKind: str | None = None
    minimumAmount: Money | None = None
    maximumAmount: Money | None = None
    allowedTerms: list[int] | None = None


class FinancingConstraints(Contract):
    productMinAmount: Money
    productMaxAmount: Money
    allowedTerms: list[int]
    allowedPurposes: list[Purpose]
    appliedAmountLimit: Money
    requiredCoverage: float
    maxNewMonthlyPayment: Money
    monthlyCashFlow: float
    totalMonthlyDebtPayment: Money
    requiredMonthlyRevenue: Money
    monthlyCoverageShortfall: Money


class Evaluation(Offer):
    coveragePasses: bool
    constraints: FinancingConstraints
    actions: list[NextAction]
    policyPasses: bool
    requiredCoverage: float
    amountLimit: Money
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


class StressScenario(Contract):
    revenueDeclinePercent: int
    monthlyRevenue: Money
    coverage: float
    coveragePasses: bool
    score: int
    policyPasses: bool
    requiredCoverage: float
    reviewRequired: bool
    assessment: str


class StressSummary(Contract):
    stressVersion: str
    calculatedAt: AwareDatetime
    assumptions: list[str]
    coverageThreshold: float
    requiredMonthlyRevenue: Money
    revenueHeadroom: float
    maxRevenueDeclinePercent: float | None
    coverageStatus: Literal["passes", "below_threshold"]
    thresholdExplanation: str
    amount: Money
    termMonths: int
    rate: Money
    policyVersion: str
    scenarios: list[StressScenario]


class RankedOffer(Contract):
    stress: StressSummary
    product: Product
    evaluation: Evaluation
    selectedEvaluation: Evaluation
    highlights: list[str]
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


class RequestedProductCheck(Contract):
    productId: str
    productName: str
    assessment: str
    policyPasses: bool
    reviewRequired: bool
    reasons: list[Reason]
    constraints: FinancingConstraints


class RequestSummary(Contract):
    status: Literal["exact_available", "exact_review", "alternatives_available", "information_required", "unavailable"]
    message: str
    exactMatchCount: Annotated[int, Field(ge=0)]
    exactReviewCount: Annotated[int, Field(ge=0)]
    otherTermCount: Annotated[int, Field(ge=0)]
    reducedAmountCount: Annotated[int, Field(ge=0)]


class RecommendationResponse(Contract):
    requestSummary: RequestSummary
    requestChecks: list[RequestedProductCheck]
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
