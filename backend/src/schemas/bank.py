from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field, field_validator
from .enums import BankDecisionAction
from .applications import ApplicationDetailResponse
from .profile import CompanyProfileResponse
from .recommendations import FinanceCalculationSchema


class BankCheckItem(BaseModel):
    name: str = Field(..., examples=["Название компании"], max_length=127)
    title: str = Field(..., examples=["Статус компании"], max_length=255)
    subtitle: str = Field(..., examples=["Активна · симулятор ФНС"], max_length=255)
    badge_type: Literal["green", "amber", "red"] = "green"
    badge_text: str = Field(..., examples=["Пройдено"], max_length=63)

    @field_validator("name", "title", "subtitle", "badge_text")
    @classmethod
    def field_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("This field can't be empty")
        return v


class BankApplicationDetailResponse(BaseModel):
    application: ApplicationDetailResponse
    company: CompanyProfileResponse
    calculation: FinanceCalculationSchema
    checks: list[BankCheckItem]
    can_approve_full: bool = Field(..., description="Доступна ли кнопка полного одобрения")
    can_offer_counter: bool = Field(..., description="Доступна ли кнопка альтернативного оффера")
    counter_offer_amount: Decimal = Field(..., ge=0, description="Сумма для кнопки 'Предложить X ₽'")


class BankDecisionRequest(BaseModel):
    action: BankDecisionAction
    custom_offer_amount: Decimal | None = Field(
        None, ge=0, description="Сумма альтернативного предложения (для action='counter')"
    )
    comment: str | None = Field(
        None, description="Причина отказа или комментарий к запросу сведений"
    )