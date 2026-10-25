"""Revenue sensitivity scenarios, not forecasts or default probabilities."""

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN
from typing import Any, Mapping

from .financing import assess_financing
from .rules import _money
from .actions import format_rubles

STRESS_VERSION = "stress-v1.2.0"


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
    threshold = Decimal(str(baseline["requiredCoverage"]))
    required = expenses + threshold * (existing + payment)
    headroom = revenue - required
    decline_percent = headroom / revenue * 100 if revenue > 0 and headroom >= 0 else None
    if headroom < 0:
        headroom_status = "below_threshold"
        headroom_message = "Исходное покрытие уже ниже требуемого порога."
    elif headroom == 0:
        headroom_status = "at_threshold"
        headroom_message = "Запас снижения выручки отсутствует: исходное покрытие ровно на пороге."
    elif decline_percent < Decimal("0.1"):
        headroom_status = "negligible"
        headroom_message = "Запас снижения выручки менее 0,1% — практически отсутствует."
    else:
        headroom_status = "positive"
        displayed_percent = str(decline_percent.quantize(Decimal("0.01"), rounding=ROUND_DOWN)).replace(".", ",")
        headroom_message = f"Запас снижения выручки до исходного порога покрытия: {displayed_percent}%. Значение округлено вниз."
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
        cash_flow = stressed_revenue - expenses
        deficit = max(Decimal(0), -cash_flow)
        if deficit > 0:
            explanation = f"Операционный дефицит — {format_rubles(deficit)} в месяц до платежей по кредитам."
        elif cash_flow == 0:
            explanation = "Выручка равна операционным расходам: средств на платежи по кредитам не остаётся."
        else:
            explanation = f"Поток до долгов — {format_rubles(cash_flow)}; все платежи по кредитам — {format_rubles(existing + payment)} в месяц."
        scenarios.append(
            {
                "revenueDeclinePercent": decline,
                "monthlyRevenue": float(stressed_revenue),
                "monthlyCashFlow": float(cash_flow),
                "operatingDeficit": float(deficit),
                "debtServiceShortfall": float(max(Decimal(0), existing + payment - cash_flow)),
                "coverageExplanation": explanation,
                "coveragePasses": stressed_revenue >= required,
                "evaluation": result,
            }
        )
    return {
        "stressVersion": STRESS_VERSION,
        "baselineMonthlyRevenue": float(revenue),
        "monthlyExpenses": float(expenses),
        "existingMonthlyPayments": float(existing),
        "newMonthlyPayment": float(payment),
        "coverageDefinition": "Покрытие = (выручка − операционные расходы) / (существующие платежи + новый платёж).",
        "headroomStatus": headroom_status,
        "headroomMessage": headroom_message,
        "calculatedAt": baseline["calculatedAt"],
        "assumptions": [
            "Снижается только выручка; расходы и существующие платежи фиксированы.",
            "Сумма, ставка, срок и нефинансовые данные не меняются.",
            "Это сценарии чувствительности, не прогноз и не вероятность дефолта.",
        ],
        "coverageThreshold": float(threshold),
        "requiredMonthlyRevenue": float(required),
        "revenueHeadroom": float(headroom),
        "maxRevenueDeclinePercent": float(decline_percent) if decline_percent is not None else None,
        "coverageStatus": "passes" if headroom >= 0 else "below_threshold",
        "thresholdExplanation": "Порог относится только к покрытию. На границе покрытие проходит; "
        "скоринг, документы и другие ограничения проверяются отдельно.",
        "scenarios": scenarios,
    }


def stress_summary(company, product, *, purpose, amount, term_months, evaluated_at):
    """Compact audited API representation; no recursive evaluations in payloads."""
    result = stress_financing(company, product, purpose=purpose, amount=amount,
                              term_months=term_months, evaluated_at=evaluated_at)
    baseline = result["scenarios"][0]["evaluation"]
    return {key: value for key, value in result.items() if key != "scenarios"} | {
        "amount": baseline["amount"], "termMonths": term_months, "rate": baseline["rate"],
        "policyVersion": baseline["policyVersion"],
        "scenarios": [{
            "revenueDeclinePercent": row["revenueDeclinePercent"],
            "monthlyRevenue": row["monthlyRevenue"],
            "monthlyCashFlow": row["monthlyCashFlow"],
            "operatingDeficit": row["operatingDeficit"],
            "debtServiceShortfall": row["debtServiceShortfall"],
            "coverageExplanation": row["coverageExplanation"],
            "coverage": row["evaluation"]["coverage"],
            "coveragePasses": row["coveragePasses"],
            "score": row["evaluation"]["scoring"]["score"],
            "policyPasses": row["evaluation"]["policyPasses"],
            "requiredCoverage": row["evaluation"]["requiredCoverage"],
            "reviewRequired": row["evaluation"]["reviewRequired"],
            "assessment": row["evaluation"]["assessment"],
        } for row in result["scenarios"]],
    }
