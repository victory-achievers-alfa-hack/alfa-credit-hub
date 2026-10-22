from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field, field_validator
from .enums import UserRole


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., examples=["client@demo.ru"])
    password: str = Field(..., min_length=1, examples=["123456"])


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserMeResponse


class UserMeResponse(BaseModel):
    id: str = Field(..., examples=["city"])
    email: EmailStr
    role: UserRole
    contact_name: str = Field(..., examples=["Александр Волков"], max_length=127)
    initials: str = Field(..., examples=["АВ"], max_length=10)
    company_name: str | None = Field(None, examples=["Магазин «Город»"], max_length=127)

    @field_validator("contact_name", "initials")
    @classmethod
    def field_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("This field can't be empty")
        return v


class FinancialProfileSchema(BaseModel):
    revenue: Decimal = Field(..., description="Месячная выручка, ₽", examples=[900000])
    expenses: Decimal = Field(..., description="Расходы без платежей по долгам, ₽", examples=[740000])
    debt: Decimal = Field(..., description="Действующие кредитные платежи, ₽", examples=[120000])
    clean: bool = Field(..., description="Без просрочек в БКИ")
    turnover: list[Decimal] = Field(..., description="Динамика выручки за 12 месяцев для графика")


class CompanyDocumentSchema(BaseModel):
    title: str = Field(..., examples=["Сведения ЕГРЮЛ / ЕГРИП"])
    source_note: str = Field(..., examples=["Синтетический документ"])
    is_valid: bool = True


class CompanyProfileResponse(BaseModel):
    id: str = Field(..., examples=["city"])
    name: str = Field(..., examples=["Магазин «Город»"], max_length=127)
    legal_name: str = Field(..., examples=["ООО «Город Ритейл»"], max_length=127)
    inn: str = Field(..., pattern=r"^\d{10,12}$", examples=["7704821934"])
    okved: str = Field(..., examples=["47.19 · Розничная торговля"])
    sector: str = Field(..., examples=["Розничная торговля"])
    since: date = Field(..., examples=["2023-03-12"])
    age_months: int = Field(..., examples=[43])
    account: str = Field(..., examples=["40702 •••• •••• 4810"])
    contact: str = Field(..., examples=["Александр Волков"], max_length=127)
    financials: FinancialProfileSchema
    documents: list[CompanyDocumentSchema]