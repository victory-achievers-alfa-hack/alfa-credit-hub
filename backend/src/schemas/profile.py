from __future__ import annotations

from datetime import date, datetime

from pydantic import EmailStr, Field, field_validator

from .base import ApiSchema, JsonDecimal
from .enums import UserRole


class LoginRequest(ApiSchema):
    email: EmailStr = Field(..., examples=["client@demo.ru"])
    password: str = Field(..., min_length=1, examples=["123456"])


class LoginResponse(ApiSchema):
    access_token: str
    token_type: str = "bearer"
    user: UserMeResponse


class UserMeResponse(ApiSchema):
    id: str = Field(..., examples=["user-client-city"])
    name: str = Field(..., examples=["Алексей Смирнов"], max_length=127)
    email: EmailStr
    role: UserRole
    company_id: str | None = Field(None, examples=["company-city"])

    @field_validator("name")
    @classmethod
    def field_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("This field can't be empty")
        return v


class FinancialProfileSchema(ApiSchema):
    revenue: JsonDecimal = Field(
        ..., description="Месячная выручка, ₽", examples=[900000]
    )
    expenses: JsonDecimal = Field(
        ..., description="Расходы без платежей по долгам, ₽", examples=[740000]
    )
    debt: JsonDecimal = Field(
        ..., description="Действующие кредитные платежи, ₽", examples=[120000]
    )
    clean: bool = Field(..., description="Без просрочек в БКИ")
    turnover: list[JsonDecimal] = Field(
        ..., description="Динамика выручки за 12 месяцев для графика"
    )


class CompanyDocumentSchema(ApiSchema):
    id: str
    name: str
    description: str
    status: str
    updated_at: datetime


class CompanyProfileResponse(ApiSchema):
    id: str = Field(..., examples=["company-city"])
    name: str = Field(..., examples=["Магазин «Город»"], max_length=127)
    legal_name: str
    inn: str = Field(..., pattern=r"^\d{10,12}$", examples=["7704821934"])
    okved: str
    registration_date: date
    account: str
    representative: str
    monthly_revenue: JsonDecimal = Field(..., ge=0)
    monthly_expenses: JsonDecimal = Field(..., ge=0)
    existing_payments: JsonDecimal = Field(..., ge=0)
    has_overdue: bool
    active: bool
    scoring_score: int = Field(..., ge=0, le=100)
    documents: list[CompanyDocumentSchema]
