from __future__ import annotations

from decimal import Decimal

from pydantic import EmailStr, Field, field_validator
from .base import ApiSchema
from .enums import UserRole


class LoginRequest(ApiSchema):
    email: EmailStr = Field(..., examples=["client@demo.ru"])
    password: str = Field(..., min_length=1, examples=["123456"])


class LoginResponse(ApiSchema):
    access_token: str | None = None
    token_type: str | None = None
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
    revenue: Decimal = Field(..., description="Месячная выручка, ₽", examples=[900000])
    expenses: Decimal = Field(
        ..., description="Расходы без платежей по долгам, ₽", examples=[740000]
    )
    debt: Decimal = Field(
        ..., description="Действующие кредитные платежи, ₽", examples=[120000]
    )
    clean: bool = Field(..., description="Без просрочек в БКИ")
    turnover: list[Decimal] = Field(
        ..., description="Динамика выручки за 12 месяцев для графика"
    )


class CompanyDocumentSchema(ApiSchema):
    id: str
    name: str
    status: str


class CompanyProfileResponse(ApiSchema):
    id: str = Field(..., examples=["company-city"])
    name: str = Field(..., examples=["Магазин «Город»"], max_length=127)
    inn: str = Field(..., pattern=r"^\d{10,12}$", examples=["7704821934"])
    industry: str
    monthly_revenue: Decimal = Field(..., ge=0)
    monthly_expenses: Decimal = Field(..., ge=0)
    current_monthly_debt_payment: Decimal = Field(..., ge=0)
    documents: list[CompanyDocumentSchema]
