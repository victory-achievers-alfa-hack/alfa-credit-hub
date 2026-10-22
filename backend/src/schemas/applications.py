from __future__ import annotations

from datetime import date, datetime, UTC
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator
from .enums import ApplicationStatus, CreditGoal


class CompanyRequest(BaseModel):
    id: int
    company_name: str = Field(..., max_length=127)
    inn: str = Field(
        ...,
        min_length=10,
        max_length=12,
        pattern=r"^\d{10}$|^\d{12}$",  # Строго 10 или 12 цифр
    )

    @field_validator("company_name")
    @classmethod
    def id_must_be_positive(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Company name can't be empty")
        return v


class ApplicationListItemResponse(BaseModel):
    id: str = Field(..., examples=["AF-1042"])
    client_id: str = Field(..., examples=["cafe"])
    company_name: str = Field(..., examples=["Кофейня «Зёрна»"], max_length=127)
    product_id: str = Field(..., examples=["investment"])
    product_name: str = Field(..., examples=["Инвестиционный кредит"], max_length=127)
    amount: Decimal = Field(..., ge=0, examples=[800000])
    offer_amount: Decimal | None = Field(None, ge=0, description="Предложенная банком сумма (если есть оффер)")
    term: int = Field(..., examples=[24])
    status: ApplicationStatus

    @field_validator("company_name", "product_name")
    @classmethod
    def field_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("This field can't be empty")
        return v

# --

class ApplicationCreateRequest(BaseModel):
    product_id: str = Field(..., examples=["working"])
    goal: CreditGoal
    amount: int = Field(..., ge=50000, le=5000000, examples=[800000])
    term: int = Field(..., examples=[24])


class ApplicationDetailResponse(ApplicationListItemResponse):
    goal: CreditGoal
    rate: float = Field(..., examples=[22.0])
    notes: str | None = Field(None, examples=["Заявка ожидает банковского решения"])
    history: list[ApplicationHistoryEvent]

# --

class ApplicationHistoryEvent(BaseModel):
    title: str = Field(..., examples=["Заявка отправлена"])
    description: str = Field(..., examples=["Данные получены от клиента"])
    creation_date: date = Field(default=datetime.now(UTC))

    @field_validator("title", "description")
    @classmethod
    def field_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("This field can't be empty")
        return v


class OfferDecisionRequest(BaseModel):
    accepted: bool = Field(..., description="True — принять (в sign), False — отказаться (в rejected)")