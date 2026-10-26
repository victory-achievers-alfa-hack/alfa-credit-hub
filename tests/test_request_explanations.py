from decimal import Decimal
import pytest
from test_financing import CAFE, CITY, PRODUCT, AT, assess
from test_review_policy import MEDIUM
from backend.src.scoring import recommend_financing


def recommend(company=CAFE, products=None, **changes):
    return recommend_financing(company, products if products is not None else [PRODUCT],
        **(dict(purpose="goods", amount=800000, term_months=24, evaluated_at=AT) | changes))


@pytest.mark.parametrize("amount,passes", [("99999.99",False),("100000",True),("100000.01",True),("3000000",True),("3000000.01",False)])
def test_catalog_amount_boundaries_are_explicit(amount, passes):
    company = CAFE | dict(monthlyRevenue=20000000, monthlyExpenses=1000000, existingPayments=0)
    result = assess(company, amount=Decimal(amount))
    reasons = [r for r in result["reasons"] if r["code"] == "AMOUNT_OUT_OF_RANGE"]
    assert bool(reasons) != passes
    assert result["policyPasses"] == passes
    if reasons:
        reason = reasons[0]
        assert reason["actual"] == float(amount)
        assert reason["minimum"] == PRODUCT["minAmount"]
        assert reason["maximum"] == PRODUCT["maxAmount"]
        assert "Запрошено" in reason["message"]


def test_same_amount_is_valid_for_only_one_product():
    express = PRODUCT | dict(id="express", minAmount=50000, rate=29)
    result = recommend(products=[PRODUCT, express], amount=50000)
    checks = {r["productId"]: r for r in result["requestChecks"]}
    assert checks["express"]["policyPasses"]
    reason = next(r for r in checks[PRODUCT["id"]]["reasons"] if r["code"] == "AMOUNT_OUT_OF_RANGE")
    assert reason["actual"] == 50000 and reason["minimum"] == 100000
    assert result["requestSummary"]["exactMatchCount"] == 1


def test_summary_distinguishes_term_changes_reduced_amount_and_review():
    alternative = recommend(CITY, amount=5000000)
    summary = alternative["requestSummary"]
    assert summary["status"] == "alternatives_available"
    assert summary["exactMatchCount"] == 0 and summary["reducedAmountCount"] > 0
    assert alternative["requestedAmount"] == 5000000
    term_change = recommend(products=[PRODUCT | {"terms": [36]}])
    assert term_change["requestSummary"]["otherTermCount"] == 1
    check = term_change["requestChecks"][0]
    assert any(r["code"] == "TERM_UNSUPPORTED" and r["allowedValues"] == [36] for r in check["reasons"])
    assert term_change["requestSummary"]["exactMatchCount"] == 0
    manual = recommend(MEDIUM, amount=100000)
    assert manual["requestSummary"]["status"] == "exact_review"
    assert manual["requestSummary"]["exactReviewCount"] == 1
    assert manual["requestSummary"]["exactMatchCount"] == 0


@pytest.mark.parametrize("company,status", [(CAFE | {"hasOverdue": True}, "unavailable"), (CAFE | {"documents": []}, "information_required")])
def test_summary_does_not_claim_available_alternatives_when_blocked(company, status):
    result = recommend(company)
    assert result["requestSummary"]["status"] == status
    assert result["requestSummary"]["reducedAmountCount"] == 0
    assert result["requestSummary"]["otherTermCount"] == 0


def test_empty_catalog_and_financial_constraints():
    result = recommend(products=[])
    assert result["requestSummary"]["status"] == "unavailable"
    assert {key: value for key, value in result["requestSummary"].items()
            if key.endswith("Count")} == dict(exactMatchCount=0, exactReviewCount=0,
                                             otherTermCount=0, reducedAmountCount=0)
    assert result["requestChecks"] == []
    assert result["groups"] == {key: [] for key in (
        "requested", "other_terms", "reduced_amount", "requires_action", "unavailable")}
    assert (result["requestedAmount"], result["requestedTermMonths"]) == (800000, 24)
    constraints = assess(CITY)["constraints"]
    assert constraints["maxNewMonthlyPayment"] == 8000
    assert constraints["monthlyCashFlow"] == 160000
    assert constraints["productMinAmount"] == 100000
    assert constraints["requiredCoverage"] == 1.25
    bad = assess(CITY | dict(monthlyExpenses=1000000))
    assert bad["constraints"]["maxNewMonthlyPayment"] == 0
    assert bad["constraints"]["monthlyCoverageShortfall"] > 0


@pytest.mark.parametrize(
    "company,term,group,offer_amount,status,counts",
    [
        pytest.param(CAFE, 24, "requested", 800000, "exact_available", (1, 0, 0, 0), id="exact"),
        pytest.param(CAFE, 36, "other_terms", 800000, "alternatives_available", (0, 0, 1, 0), id="term-only"),
        pytest.param(CITY, 24, "reduced_amount", 150000, "alternatives_available", (0, 0, 0, 1), id="amount-only"),
        pytest.param(CITY, 36, "reduced_amount", 200000, "alternatives_available", (0, 0, 0, 1), id="amount-and-term"),
        pytest.param(CITY, 12, "unavailable", 800000, "unavailable", (0, 0, 0, 0), id="no-affordable-amount"),
    ],
)
def test_request_classification_and_summary(company, term, group, offer_amount, status, counts):
    result = recommend(company, products=[PRODUCT | {"terms": [term]}])
    assert (result["requestedAmount"], result["requestedTermMonths"]) == (800000, 24)
    assert {key: len(items) for key, items in result["groups"].items()} == {
        key: int(key == group) for key in result["groups"]}
    item, = result["groups"][group]
    assert item["group"] == group
    assert (item["offer"]["amount"], item["offer"]["termMonths"]) == (offer_amount, term)
    assert item["termChanged"] == (term != 24)
    assert item["amountShortfall"] == 800000 - offer_amount
    assert item["evaluation"]["amount"] == 800000
    assert item["evaluation"]["termMonths"] == term
    selected = item["selectedEvaluation"]
    assert (selected["amount"], selected["termMonths"]) == (offer_amount, term)
    assert selected["policyPasses"] == (group != "unavailable")
    if offer_amount < 800000:
        assert not item["evaluation"]["policyPasses"]
        assert item["evaluation"]["alternative"]["amount"] == offer_amount
        assert selected["alternative"] is None
        assert selected["eligible"] and item["offer"]["eligible"]
    check, = result["requestChecks"]
    if term != 24:
        assert not check["policyPasses"]
        assert any(reason["code"] == "TERM_UNSUPPORTED" for reason in check["reasons"])
    summary = result["requestSummary"]
    assert summary["status"] == status
    assert tuple(summary[key] for key in (
        "exactMatchCount", "exactReviewCount", "otherTermCount", "reducedAmountCount")) == counts


@pytest.mark.parametrize(
    "amount,status,counts",
    [(100000, "exact_review", (0, 1, 2, 0)),
     (800000, "alternatives_available", (0, 0, 1, 2))],
)
def test_summary_counts_only_passing_review_conditions(amount, status, counts):
    result = recommend(MEDIUM, amount=amount)
    assert all(not result["groups"][key] for key in ("requested", "other_terms", "reduced_amount"))
    items = result["groups"]["requires_action"]
    assert len(items) == 3
    assert all(item["selectedEvaluation"]["policyPasses"] for item in items)
    assert all(item["offer"]["reviewRequired"] and not item["offer"]["eligible"] for item in items)
    summary = result["requestSummary"]
    assert summary["status"] == status
    assert tuple(summary[key] for key in (
        "exactMatchCount", "exactReviewCount", "otherTermCount", "reducedAmountCount")) == counts
    if amount == 800000:
        assert not result["requestChecks"][0]["policyPasses"]
        assert any(item["termChanged"] and item["offer"]["amount"] < amount for item in items)


def test_rounded_coverage_never_overrules_exact_money_check():
    company = CAFE | dict(monthlyRevenue=Decimal('1000000000000'), monthlyExpenses=0, existingPayments=Decimal('799999999999.51'))
    product = PRODUCT | dict(minAmount=Decimal('.01'), maxAmount=1000, rate=0, terms=[1])
    result = assess(company, product, amount=Decimal('.50'), term_months=1)
    # Two-decimal display rounds to 1.25; exact debt exceeds the budget by 0.01.
    assert round(result['coverage'], 2) == 1.25
    assert result['coveragePasses'] is False
    assert result['constraints']['monthlyCoverageShortfall'] == 0.0125
    assert result['policyPasses'] is False
    assert any(c['id'] == 'coverage' and c['state'] == 'warning' for c in result['checks'])
