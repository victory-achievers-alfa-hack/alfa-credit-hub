from datetime import datetime
from decimal import Decimal

from pydantic import Field

from .base import ApiSchema
from .enums import ApplicationStatus, CreditGoal, UserRole


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


class ApplicationEventResponse(ApiSchema):
    id: str
    type: str
    description: str
    old_status: ApplicationStatus | None = None
    new_status: ApplicationStatus | None = None
    actor_id: str
    actor_role: UserRole
    created_at: datetime


class ApplicationCheckResponse(ApiSchema):
    name: str
    status: str
    details: str | None = None


class ApplicationOfferResponse(ApiSchema):
    amount: Decimal = Field(..., ge=0)
    term_months: int = Field(..., gt=0)
    rate: Decimal = Field(..., ge=0)
    monthly_payment: Decimal = Field(..., ge=0)
    expires_at: datetime | None = None


class ApplicationListItemResponse(ApiSchema):
    id: str = Field(..., examples=["APP-2026-003"])
    company_id: str
    company_name: str
    product_id: str
    product_name: str
    purpose: CreditGoal
    amount: Decimal = Field(..., ge=0)
    term_months: int = Field(..., gt=0)
    status: ApplicationStatus
    updated_at: datetime


class ApplicationDetailResponse(ApplicationListItemResponse):
    rate: Decimal = Field(..., ge=0)
    monthly_payment: Decimal = Field(..., ge=0)
    coverage: Decimal
    score: int = Field(..., ge=0, le=100)
    risk: str
    explanation: str
    factors: list[str]
    checks: list[ApplicationCheckResponse]
    active_offer: ApplicationOfferResponse | None = None
    bank_comment: str | None = None
    history: list[ApplicationEventResponse]


class ApplicationListResponse(ApiSchema):
    items: list[ApplicationListItemResponse]
    total: int = Field(..., ge=0)
    limit: int = Field(..., gt=0)
    offset: int = Field(..., ge=0)


class ApplicationListQuery(ApiSchema):
    status: ApplicationStatus | None = None
    limit: int = Field(default=20, gt=0, le=100)
    offset: int = Field(default=0, ge=0)
