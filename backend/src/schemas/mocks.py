from datetime import date, UTC, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class FnsMockResponse(BaseModel):
    inn: str = Field( ..., pattern=r"^\d{10,12}$", examples=["7704821934"])
    legal_name: str = Field(..., max_length=127)
    is_active: bool = True
    registered_since: date = datetime.now(UTC)
    okved: str

    @field_validator("legal_name")
    @classmethod
    def field_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("This field can't be empty")
        return v


class BkiMockResponse(BaseModel):
    inn: str = Field( ..., pattern=r"^\d{10,12}$", examples=["7704821934"])
    has_delinquencies: bool = Field(..., description="Есть ли просрочки (!clean)")
    monthly_debt_load: Decimal = Field(..., ge=0, description="Текущие платежи в месяц, ₽")