"""Project heuristics, not calibrated default probabilities or bank policy."""

from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

MODEL_VERSION = "rules-v1.0.0"
FEATURE_VERSION = "company-v1"
LOW_RISK_MIN = 70
MEDIUM_RISK_MIN = 50


class InputError(ValueError):
    """Invalid or missing input: request corrected data, never assume zero."""

    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(f"{field}: {message}")


def _money(data: Mapping[str, Any], field: str) -> Decimal:
    raw = data.get(field)
    if isinstance(raw, bool) or not isinstance(raw, (str, int, float, Decimal)):
        raise InputError(field, "required nonnegative amount in rubles")
    try:
        value = Decimal(str(raw))
    except InvalidOperation as exc:
        raise InputError(field, "invalid number") from exc
    if not value.is_finite() or value < 0 or value > Decimal("1000000000000"):
        raise InputError(field, "must be finite and between 0 and 1e12 rubles")
    if value != value.quantize(Decimal("0.01")):
        raise InputError(field, "at most two decimal places")
    return value


def score_company(company: Mapping[str, Any], *, evaluated_at: datetime) -> dict[str, Any]:
    """Score a company at an explicit instant; identical input yields identical output.

    Accepts frontend field names. Ignores legacy scoringScore and loan terms.
    Requires monthly operating expenses excluding all debt service.
    hasOverdue means outstanding overdue debt at the evaluation instant.
    """
    if not isinstance(evaluated_at, datetime) or evaluated_at.utcoffset() is None:
        raise InputError("evaluated_at", "timezone-aware datetime required")
    instant = evaluated_at.astimezone(timezone.utc)
    revenue = _money(company, "monthlyRevenue")
    expenses = _money(company, "monthlyExpenses")
    debt = _money(company, "existingPayments")
    overdue = company.get("hasOverdue")
    if not isinstance(overdue, bool):
        raise InputError("hasOverdue", "explicit boolean required")
    raw_date = company.get("registrationDate")
    try:
        if not isinstance(raw_date, str) or len(raw_date) != 10:
            raise ValueError
        registered = date.fromisoformat(raw_date)
        if registered.isoformat() != raw_date:
            raise ValueError
    except ValueError as exc:
        raise InputError("registrationDate", "YYYY-MM-DD required") from exc
    today = instant.date()
    if registered > today:
        raise InputError("registrationDate", "cannot be in the future")
    age_months = (today.year - registered.year) * 12 + today.month - registered.month
    age_months -= today.day < registered.day
    flow = revenue - expenses
    margin = flow / revenue if revenue > 0 else None
    coverage = flow / debt if debt > 0 else None

    history_points = 0 if overdue else 30
    margin_points = (25 if margin >= Decimal("0.20") else
                     18 if margin >= Decimal("0.10") else
                     10 if margin > 0 else 0) if margin is not None else 0
    if flow <= 0:
        debt_points = 0
    elif debt == 0:
        debt_points = 30
    else:
        debt_points = (30 if coverage >= 2 else 22 if coverage >= Decimal("1.25")
                       else 10 if coverage >= 1 else 0)
    age_points = 15 if age_months >= 36 else 10 if age_months >= 12 else 5 if age_months >= 6 else 0

    def factor(code: str, label: str, value: str, points: int, maximum: int) -> dict[str, Any]:
        return {"code": code, "label": label, "value": value,
                "positive": points >= maximum / 2, "points": points, "maxPoints": maximum}

    factors = [
        factor("PAYMENT_HISTORY", "Текущая просрочка", "Есть" if overdue else "Нет", history_points, 30),
        factor("OPERATING_MARGIN", "Операционная маржа",
               f"{margin * 100:.2f}%" if margin is not None else "Не определена: нулевая выручка", margin_points, 25),
        factor("EXISTING_DEBT_COVERAGE", "Покрытие существующих платежей",
               f"{coverage:.2f}×" if coverage is not None else "Существующих платежей нет", debt_points, 30),
        factor("BUSINESS_AGE", "Возраст бизнеса", f"{age_months} полных месяцев", age_points, 15),
    ]
    score = sum(item["points"] for item in factors)
    risk = "low" if score >= LOW_RISK_MIN else "medium" if score >= MEDIUM_RISK_MIN else "high"
    labels = {"low": "устойчивый", "medium": "промежуточный", "high": "слабый"}
    return {
        "score": score,
        "riskLevel": risk,
        "summary": f"Профиль по демонстрационным правилам: {labels[risk]}, {score}/100. "
                   "Это не вероятность дефолта и не решение об одобрении кредита.",
        "factors": factors,
        "modelVersion": MODEL_VERSION,
        "featureVersion": FEATURE_VERSION,
        "calculatedAt": instant.isoformat().replace("+00:00", "Z"),
        "eventProbability": None,
    }
