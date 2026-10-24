"""Run from repository root: python -m examples.financing_demo.

Synthetic examples only. Does not connect to a bank, database or HTTP server.
"""

import json
from datetime import datetime, timezone

from backend.src.scoring import assess_financing


def demo_results():
    at = datetime(2026, 10, 23, tzinfo=timezone.utc)
    documents = [{"id": key, "status": "ready"}
                 for key in ("registry", "statement", "reporting", "bki")]
    product = dict(id="working-capital", name="Оборотный кредит", minAmount=100000,
                   maxAmount=3000000, rate=24, terms=[12, 24, 36], purposes=["goods", "cash_gap"])
    city = dict(registrationDate="2019-03-18", monthlyRevenue=900000,
                monthlyExpenses=740000, existingPayments=120000,
                hasOverdue=False, active=True, documents=documents)
    cafe = city | dict(registrationDate="2018-07-04", monthlyRevenue=1200000,
                       monthlyExpenses=850000, existingPayments=70000)
    vector = city | dict(registrationDate="2025-05-12", monthlyRevenue=500000,
                         monthlyExpenses=490000, existingPayments=90000, hasOverdue=True)
    cases = [("Город", city, "alternative"), ("Зёрна", cafe, "eligible"),
             ("Вектор", vector, "blocked"),
             ("Новый клиент без документов", cafe | {"documents": []}, "need_info")]
    results = []
    for name, company, expected in cases:
        result = assess_financing(company, product, purpose="goods", amount=800000,
                                  term_months=24, evaluated_at=at)
        if result["assessment"] != expected:
            raise AssertionError(f"{name}: expected {expected}, got {result['assessment']}")
        results.append({"scenario": name, "expectedAssessment": expected, "result": result})
    return results


if __name__ == "__main__":
    print(json.dumps(demo_results(), ensure_ascii=False, indent=2, allow_nan=False))
