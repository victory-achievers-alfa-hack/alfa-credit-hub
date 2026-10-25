from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import Field

from .base import ApiSchema, JsonDecimal
from backend.src.recommendation_contract import NextAction, StressSummary
from .enums import ApplicationStatus, CreditGoal


class ApplicationCreateRequest(ApiSchema):
    product_id: str = Field(..., min_length=1, examples=["working-capital"])
    purpose: CreditGoal
    amount: Decimal = Field(..., ge=50000, le=5000000, examples=[800000])
    term_months: int = Field(..., gt=0, examples=[24])


class AdditionalInfoRequest(ApiSchema):
    comment: str = Field(..., min_length=1, max_length=2000)
    document_ids: list[str] = Field(default_factory=list)


class OfferDecisionRequest(ApiSchema):
    accepted: bool = Field(..., description="Принимает ли клиент оффер")


class ScoringFactorResponse(ApiSchema):
    label: str
    value: str
    positive: bool
    code: str | None = None
    points: int | None = None
    max_points: int | None = None


class ScoringResultResponse(ApiSchema):
    score: int = Field(..., ge=0, le=100)
    risk_level: Literal["low", "medium", "high"]
    summary: str
    model_version: str | None = None
    feature_version: str | None = None
    calculated_at: datetime | None = None
    event_probability: float | None = None
    factors: list[ScoringFactorResponse]


class ApplicationCheckResponse(ApiSchema):
    id: str
    label: str
    value: str
    description: str
    state: Literal["success", "warning", "error"]


class ApplicationEventResponse(ApiSchema):
    id: str
    status: ApplicationStatus
    title: str
    description: str
    actor: str
    created_at: datetime


class ApplicationOfferResponse(ApiSchema):
    id: str
    amount: JsonDecimal = Field(..., ge=0)
    term_months: int = Field(..., gt=0)
    rate: JsonDecimal = Field(..., ge=0)
    monthly_payment: JsonDecimal = Field(..., ge=0)
    reason: str
    created_at: datetime


class ApplicationListItemResponse(ApiSchema):
    id: str = Field(..., examples=["APP-2026-003"])
    company_id: str
    company_name: str
    product_id: str
    product_name: str
    purpose: CreditGoal
    amount: JsonDecimal = Field(..., ge=0)
    term_months: int = Field(..., gt=0)
    status: ApplicationStatus
    updated_at: datetime


class ApplicationDetailResponse(ApiSchema):
    stress: StressSummary | None = None
    actions: list[NextAction] = Field(default_factory=list)
    required_coverage: float = 1.25
    id: str
    company_id: str
    product_id: str
    product_name: str
    purpose: CreditGoal
    requested_amount: JsonDecimal = Field(..., ge=0)
    requested_term_months: int = Field(..., gt=0)
    requested_rate: JsonDecimal = Field(..., ge=0)
    requested_monthly_payment: JsonDecimal = Field(..., ge=0)
    coverage: JsonDecimal
    status: ApplicationStatus
    scoring: ScoringResultResponse
    checks: list[ApplicationCheckResponse]
    offer: ApplicationOfferResponse | None = None
    bank_comment: str | None = None
    info_request: str | None = None
    created_at: datetime
    updated_at: datetime
    events: list[ApplicationEventResponse]


class ApplicationListResponse(ApiSchema):
    items: list[ApplicationListItemResponse]
    total: int = Field(..., ge=0)
    limit: int = Field(..., gt=0)
    offset: int = Field(..., ge=0)


class ApplicationListQuery(ApiSchema):
    status: ApplicationStatus | None = None
    limit: int = Field(default=20, gt=0, le=100)
    offset: int = Field(default=0, ge=0)
