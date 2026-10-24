"""Deterministic catalogue recommendations; never an approval decision."""

from copy import deepcopy
from datetime import datetime
from typing import Any, Mapping

from .financing import assess_financing, _validate_product, _term, _documents_ready
from .rules import InputError, _money, score_company

RANKING_VERSION = "ranking-v1.0.0"


def recommend_financing(
    company: Mapping[str, Any],
    products: list,
    *,
    purpose: str,
    amount: Any,
    term_months: int,
    evaluated_at: datetime,
    preference: str = "min_interest",
) -> dict[str, Any]:
    """Rank within explicit groups, including all supported alternative terms.

    Reduced amounts are ordered by amount descending before monetary preference:
    a tiny loan must not win merely because its absolute interest is lower.
    """
    if preference not in ("min_interest", "min_payment"):
        raise InputError("preference", "min_interest or min_payment required")
    principal = _money({"amount": amount}, "amount")
    if principal <= 0:
        raise InputError("amount", "positive amount required")
    _term(term_months)
    if purpose not in ("goods", "equipment", "cash_gap"):
        raise InputError("purpose", "unsupported purpose")
    scoring = score_company(company, evaluated_at=evaluated_at)
    if type(company.get("active")) is not bool:
        raise InputError("active", "explicit boolean required")
    _documents_ready(company)
    if not isinstance(products, list):
        raise InputError("products", "list required")
    seen = set()
    for product in products:
        if not isinstance(product, Mapping):
            raise InputError("products", "product objects required")
        _validate_product(product)
        if product["id"] in seen:
            raise InputError("products", "duplicate product id")
        seen.add(product["id"])
    groups = {
        key: []
        for key in (
            "requested",
            "other_terms",
            "reduced_amount",
            "requires_action",
            "unavailable",
        )
    }
    metric = "interestAmount" if preference == "min_interest" else "monthlyPayment"
    secondary = "monthlyPayment" if preference == "min_interest" else "interestAmount"
    for product in products:
        if purpose not in product["purposes"]:
            # Retain an explanation without generating irrelevant term variants.
            terms = [term_months]
        else:
            terms = sorted(set(product["terms"]))
        for term in terms:
            result = assess_financing(
                company,
                product,
                purpose=purpose,
                amount=principal,
                term_months=term,
                evaluated_at=evaluated_at,
            )
            if purpose not in product["purposes"]:
                group = "unavailable"
            elif result["eligible"]:
                group = "requested" if term == term_months else "other_terms"
            elif result["alternative"]:
                group = "reduced_amount"
            elif result["assessment"] in ("need_info", "manual_review", "blocked"):
                group = "requires_action"
            else:
                group = "unavailable"
            offer = result["alternative"] if group == "reduced_amount" else result
            item = {
                "product": deepcopy(dict(product)),
                "evaluation": result,
                "offer": {
                    k: offer[k]
                    for k in (
                        "amount",
                        "termMonths",
                        "rate",
                        "monthlyPayment",
                        "lastPayment",
                        "totalRepayment",
                        "interestAmount",
                        "coverage",
                        "eligible",
                    )
                },
                "termChanged": term != term_months,
                "amountShortfall": float(principal - _money(offer, "amount")),
                "group": group,
            }
            groups[group].append(item)
    for group, items in groups.items():
        if group in ("requires_action", "unavailable"):
            items.sort(key=lambda x: (x["product"]["id"], x["offer"]["termMonths"]))
        else:
            items.sort(
                key=lambda x: (
                    -x["offer"]["amount"] if group == "reduced_amount" else 0,
                    x["offer"][metric],
                    x["offer"][secondary],
                    abs(x["offer"]["termMonths"] - term_months),
                    x["offer"]["termMonths"],
                    x["product"]["id"],
                )
            )
        for rank, item in enumerate(items, 1):
            item["rankInGroup"] = rank
            item["rankingReason"] = (
                "Нужны действия или другие условия; порядок по продукту и сроку не означает рекомендацию."
                if group in ("requires_action", "unavailable")
                else (
                    "Сначала большая доступная сумма; "
                    if group == "reduced_amount"
                    else ""
                )
                + (
                    "меньшая переплата"
                    if preference == "min_interest"
                    else "меньший ежемесячный платёж"
                )
                + " внутри группы. Предварительная оценка, не одобрение банка."
            )
    return {
        "rankingVersion": RANKING_VERSION,
        "preference": preference,
        "requestedAmount": float(principal),
        "requestedTermMonths": term_months,
        "calculatedAt": scoring["calculatedAt"],
        "groups": groups,
    }
