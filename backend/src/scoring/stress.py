"""Revenue sensitivity scenarios, not forecasts or default probabilities."""

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Mapping

from .financing import assess_financing, MIN_COVERAGE
from .rules import _money

STRESS_VERSION = "stress-v1.0.0"


def stress_financing(
    company: Mapping[str, Any],
    product: Mapping[str, Any],
    *,
    purpose: str,
    amount: Any,
    term_months: int,
    evaluated_at: datetime,
) -> dict[str, Any]:
    """Re-evaluate the SAME requested amount at 0/10/20/30% revenue declines.

    Threshold is specifically for payment coverage, not overall eligibility.
    Expenses, existing debt service, product terms and nonfinancial data are fixed.
    """
    baseline = assess_financing(
        company,
        product,
        purpose=purpose,
        amount=amount,
        term_months=term_months,
        evaluated_at=evaluated_at,
    )
    revenue = _money(company, "monthlyRevenue")
    expenses = _money(company, "monthlyExpenses")
    existing = _money(company, "existingPayments")
    payment = Decimal(str(baseline["monthlyPayment"]))
    required = expenses + MIN_COVERAGE * (existing + payment)
    headroom = revenue - required
    scenarios = []
    for decline in (0, 10, 20, 30):
        stressed_revenue = (revenue * (1 - Decimal(decline) / 100)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        result = (
            baseline
            if decline == 0
            else assess_financing(
                dict(company) | {"monthlyRevenue": stressed_revenue},
                product,
                purpose=purpose,
                amount=amount,
                term_months=term_months,
                evaluated_at=evaluated_at,
            )
        )
        scenarios.append(
            {
                "revenueDeclinePercent": decline,
                "monthlyRevenue": float(stressed_revenue),
                "coveragePasses": stressed_revenue >= required,
                "evaluation": result,
            }
        )
    return {
        "stressVersion": STRESS_VERSION,
        "calculatedAt": baseline["calculatedAt"],
        "assumptions": [
            "Снижается только выручка; расходы и существующие платежи фиксированы.",
            "Сумма, ставка, срок и нефинансовые данные не меняются.",
            "Это сценарии чувствительности, не прогноз и не вероятность дефолта.",
        ],
        "coverageThreshold": float(MIN_COVERAGE),
        "requiredMonthlyRevenue": float(required),
        "revenueHeadroom": float(headroom),
        "maxRevenueDeclinePercent": float(headroom / revenue * 100)
        if revenue > 0 and headroom >= 0
        else None,
        "coverageStatus": "passes" if headroom >= 0 else "below_threshold",
        "thresholdExplanation": "Порог относится только к покрытию. На границе покрытие проходит; "
        "скоринг, документы и другие ограничения проверяются отдельно.",
        "scenarios": scenarios,
    }
