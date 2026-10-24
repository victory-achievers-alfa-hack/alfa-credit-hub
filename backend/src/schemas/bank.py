from decimal import Decimal

from pydantic import Field, model_validator

from .applications import ApplicationDetailResponse
from .base import ApiSchema, JsonDecimal
from .enums import ApplicationStatus, BankDecisionKind
from .profile import CompanyProfileResponse


class BankApplicationListItemResponse(ApiSchema):
    id: str
    company_id: str
    company_name: str
    product_name: str
    amount: JsonDecimal = Field(..., ge=0)
    status: ApplicationStatus


class BankApplicationListResponse(ApiSchema):
    items: list[BankApplicationListItemResponse]
    total: int = Field(..., ge=0)


class BankApplicationDetailResponse(ApiSchema):
    application: ApplicationDetailResponse
    company: CompanyProfileResponse


class BankDecisionRequest(ApiSchema):
    kind: BankDecisionKind
    amount: Decimal | None = Field(None, gt=0)
    term_months: int | None = Field(None, gt=0)
    rate: Decimal | None = Field(None, ge=0)
    comment: str | None = Field(None, max_length=2000)

    @model_validator(mode="after")
    def validate_decision_fields(self):
        if self.kind == BankDecisionKind.ALTERNATIVE:
            if self.amount is None or self.term_months is None or self.rate is None:
                raise ValueError(
                    "amount, termMonths and rate are required for an offer"
                )
            if not self.comment:
                raise ValueError("comment is required for an alternative offer")
        if (
            self.kind in (BankDecisionKind.NEED_INFO, BankDecisionKind.REJECT)
            and not self.comment
        ):
            raise ValueError("comment is required for this decision")
        return self
