"""Indicative monthly annuity calculations and versioned prequalification policy.

No database mutations, automatic approvals, external services or PD estimates.
"""

from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP, ROUND_DOWN, localcontext
from datetime import datetime
from typing import Any, Mapping

from .rules import InputError, _money, score_company
from .actions import next_actions

POLICY_VERSION = "financing-v1.2.0"
MIN_COVERAGE = Decimal("1.25")
MIN_SCORE = 70
REVIEW_MIN_SCORE = 50
REVIEW_MIN_COVERAGE = Decimal("1.50")
REVIEW_REVENUE_SHARE = Decimal("0.50")
AMOUNT_STEP = Decimal("10000")
REQUIRED_DOCUMENTS = frozenset({"registry", "statement", "reporting", "bki"})
CENT = Decimal("0.01")


def _term(value: Any) -> int:
    if type(value) is not int or not 1 <= value <= 120:
        raise InputError("termMonths", "integer between 1 and 120 required")
    return value


def _rate(value: Any) -> Decimal:
    rate = _money({"rate": value}, "rate")
    if rate > 100:
        raise InputError("rate", "annual percentage must be between 0 and 100")
    return rate


def _payment(amount: Decimal, rate: Decimal, term: int) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = 40
        monthly = rate / 1200
        payment = (
            amount / term
            if monthly == 0
            else amount * monthly / (1 - (1 + monthly) ** -term)
        )
        return payment.quantize(CENT, rounding=ROUND_CEILING)


def loan_quote(amount: Any, annual_rate: Any, term_months: int) -> dict[str, Any]:
    """Equal monthly periods, no fees; regular payment rounded UP to a kopeck.

    Accrue interest at full Decimal precision, adjust last payment to extinguish
    balance. This is an indicative calculation, not a day-count bank contract.
    """
    principal = _money({"amount": amount}, "amount")
    if principal <= 0:
        raise InputError("amount", "positive amount required")
    term, rate = _term(term_months), _rate(annual_rate)
    payment = _payment(principal, rate, term)
    with localcontext() as ctx:
        ctx.prec = 40
        balance, total = principal, Decimal(0)
        last = Decimal(0)
        for month in range(1, term + 1):
            due = balance * (1 + rate / 1200)
            last = min(payment, due).quantize(CENT, rounding=ROUND_HALF_UP)
            total += last
            balance = max(Decimal(0), due - last)
    return {
        "amount": float(principal),
        "rate": float(rate),
        "termMonths": term,
        "monthlyPayment": float(payment),
        "lastPayment": float(last),
        "totalRepayment": float(total),
        "interestAmount": float(total - principal),
    }


def _validate_product(product: Mapping[str, Any]) -> tuple[Decimal, Decimal, Decimal]:
    for field in ("id", "name"):
        if not isinstance(product.get(field), str) or not product[field].strip():
            raise InputError(f"product.{field}", "nonempty string required")
    minimum, maximum = _money(product, "minAmount"), _money(product, "maxAmount")
    if minimum <= 0 or maximum < minimum:
        raise InputError("product.amountRange", "0 < minAmount <= maxAmount required")
    terms, purposes = product.get("terms"), product.get("purposes")
    if not isinstance(terms, list) or not terms:
        raise InputError("product.terms", "nonempty list required")
    for term in terms:
        _term(term)
    if (
        not isinstance(purposes, list)
        or not purposes
        or any(p not in ("goods", "equipment", "cash_gap") for p in purposes)
    ):
        raise InputError("product.purposes", "supported purposes required")
    return minimum, maximum, _rate(product.get("rate"))


def _documents_ready(company: Mapping[str, Any]) -> bool:
    documents = company.get("documents")
    if documents is None:
        return False
    if not isinstance(documents, list):
        raise InputError("documents", "list required")
    seen = {}
    seen_ids = set()
    for document in documents:
        if not isinstance(document, Mapping) or not isinstance(document.get("id"), str):
            raise InputError("documents", "each document must have a string id")
        kind = document.get("kind", document["id"])
        if not isinstance(kind, str) or not kind:
            raise InputError("documents", "each document must have a kind")
        if (
            document["id"] in seen_ids
            or kind in seen
            or document.get("status") not in ("ready", "verified", "attention")
        ):
            raise InputError(
                "documents", "unique ids and recognized document statuses required"
            )
        seen_ids.add(document["id"])
        seen[kind] = document["status"]
    return all(seen.get(key) in ("ready", "verified") for key in REQUIRED_DOCUMENTS)


def _affordable_amount(
    budget: Decimal, maximum: Decimal, minimum: Decimal, rate: Decimal, term: int
) -> Decimal | None:
    """Maximum 10,000-ruble grid amount passing the actual rounded-payment check."""
    lo, hi = 0, int(maximum // AMOUNT_STEP)
    while lo < hi:
        middle = (lo + hi + 1) // 2
        if _payment(AMOUNT_STEP * middle, rate, term) <= budget:
            lo = middle
        else:
            hi = middle - 1
    candidate = AMOUNT_STEP * lo
    if candidate >= minimum:
        return candidate
    # A product minimum need not be a multiple of the proposal step.
    if minimum <= maximum and _payment(minimum, rate, term) <= budget:
        return minimum
    return None


def assess_financing(
    company: Mapping[str, Any],
    product: Mapping[str, Any],
    *,
    purpose: str,
    amount: Any,
    term_months: int,
    evaluated_at: datetime,
) -> dict[str, Any]:
    """Assess one offer, retaining reason codes and separating score from policy.

    assessment is NOT an application status: eligible, alternative, need_info,
    manual_review, blocked, unavailable. Only the bank workflow changes status.
    """
    minimum, maximum, rate = _validate_product(product)
    principal = _money({"amount": amount}, "amount")
    if principal <= 0:
        raise InputError("amount", "positive amount required")
    term = _term(term_months)
    if purpose not in ("goods", "equipment", "cash_gap"):
        raise InputError("purpose", "unsupported purpose")
    if type(company.get("active")) is not bool:
        raise InputError("active", "explicit boolean required")
    docs_ready = _documents_ready(company)
    scoring = score_company(company, evaluated_at=evaluated_at)
    flow = _money(company, "monthlyRevenue") - _money(company, "monthlyExpenses")
    existing = _money(company, "existingPayments")
    quote = loan_quote(principal, rate, term)
    payment = Decimal(str(quote["monthlyPayment"]))
    denominator = existing + payment  # Positive principal implies positive payment.
    coverage = flow / denominator
    # Compare exact Decimal operands, never the rounded display ratio.
    review_required = REVIEW_MIN_SCORE <= scoring["score"] < MIN_SCORE
    threshold = REVIEW_MIN_COVERAGE if review_required else MIN_COVERAGE
    amount_limit = min(maximum, (_money(company, "monthlyRevenue") * REVIEW_REVENUE_SHARE).quantize(CENT, rounding=ROUND_DOWN)) if review_required else maximum
    covered = flow >= threshold * denominator
    reasons = []

    def reason(code: str, message: str):
        reasons.append({"code": code, "message": message})

    if not company["active"]:
        reason(
            "INACTIVE_COMPANY",
            "Компания не действует; предварительное прохождение заблокировано.",
        )
    if company["hasOverdue"]:
        reason(
            "CURRENT_OVERDUE",
            "Есть текущая просрочка; уменьшение суммы не снимает ограничение.",
        )
    if not docs_ready:
        reason(
            "DOCUMENTS_REQUIRED",
            "Нужны готовые сведения реестра, БКИ, выписка и финансовая отчётность.",
        )
    if scoring["score"] < REVIEW_MIN_SCORE:
        reason("SCORE_TOO_LOW", "Балл ниже 50: кредитное предложение недоступно по текущей политике.")
    elif review_required:
        reason("SCORE_REVIEW", "Балл 50–69: решение сотрудника с обоснованием, покрытие от 1,5× и сумма не более 50% месячной выручки.")
        if principal > amount_limit:
            reason("REVIEW_AMOUNT_LIMIT", "Сумма превышает лимит рассмотрения: 50% месячной выручки.")
    compatible = purpose in product["purposes"] and term in product["terms"]
    if purpose not in product["purposes"]:
        reason("PURPOSE_MISMATCH", "Продукт не соответствует цели финансирования.")
    if term not in product["terms"]:
        reason("TERM_UNSUPPORTED", "Выбранный срок не предусмотрен продуктом.")
    if not minimum <= principal <= maximum:
        reason("AMOUNT_OUT_OF_RANGE", "Запрошенная сумма вне диапазона продукта.")
    if not covered:
        reason("INSUFFICIENT_COVERAGE", f"Покрытие всех платежей ниже {threshold}×.")

    alternative = None
    if not company["active"] or company["hasOverdue"] or scoring["score"] < REVIEW_MIN_SCORE:
        assessment = "blocked"
    elif not docs_ready:
        assessment = "need_info"
    elif not compatible or principal < minimum:
        assessment = "unavailable"
    elif principal <= amount_limit and covered:
        assessment = "manual_review" if review_required else "eligible"
    else:
        budget = flow / threshold - existing
        candidate = _affordable_amount(
            budget, min(principal, amount_limit), minimum, rate, term
        )
        if candidate is not None and candidate < principal:
            alt_quote = loan_quote(candidate, rate, term)
            alt_payment = Decimal(str(alt_quote["monthlyPayment"]))
            if flow < threshold * (existing + alt_payment):
                raise ArithmeticError("alternative violates coverage policy")
            alternative = {
                **alt_quote,
                "coverage": float(flow / (existing + alt_payment)),
                "eligible": not review_required,
                "reviewRequired": review_required,
            }
            assessment = "manual_review" if review_required else "alternative"
            reason(
                "LOWER_AMOUNT_AVAILABLE",
                "Доступна меньшая сумма на том же сроке; требуется согласие клиента.",
            )
        else:
            assessment = "unavailable"
            reason(
                "NO_AFFORDABLE_AMOUNT",
                "Нет доступной суммы в пределах продукта на выбранном сроке.",
            )
    if assessment == "eligible":
        reason(
            "PREQUALIFIED",
            "Вариант проходит предварительные правила; это не окончательное одобрение.",
        )
    checks = [
        {
            "id": "registry",
            "label": "Реестр компаний",
            "value": "Компания действует" if company["active"] else "Есть ограничения",
            "description": "Статус и реквизиты сверены с синтетическим реестром",
            "state": "success" if company["active"] else "error",
        },
        {
            "id": "bki",
            "label": "Кредитная история",
            "value": "Есть просрочки" if company["hasOverdue"] else "Без просрочек",
            "description": "Результат локального симулятора БКИ",
            "state": "error" if company["hasOverdue"] else "success",
        },
        {
            "id": "documents",
            "label": "Комплект документов",
            "value": "Полный комплект" if docs_ready else "Нужно уточнение",
            "description": "Проверены синтетические документы компании",
            "state": "success" if docs_ready else "warning",
        },
        {
            "id": "coverage",
            "label": "Покрытие платежей",
            "value": f"{coverage:.2f}×",
            "description": f"Требуемое покрытие для текущего профиля — {threshold}×",
            "state": "success" if covered else "warning",
        },
    ]
    result = {
        "productId": product["id"],
        "purpose": purpose,
        **quote,
        "coverage": float(coverage),
        "eligible": assessment == "eligible",
        "reviewRequired": review_required,
        "policyPasses": assessment in ("eligible", "manual_review") and alternative is None,
        "requiredCoverage": float(threshold),
        "amountLimit": float(amount_limit),
        "assessment": assessment,
        "reasons": reasons,
        "checks": checks,
        "alternative": alternative,
        "recommendedAmount": alternative["amount"] if alternative else None,
        "scoring": scoring,
        "policyVersion": POLICY_VERSION,
        "calculatedAt": scoring["calculatedAt"],
    }

    result["actions"] = next_actions(company, result)
    return result
