from copy import deepcopy
from decimal import Decimal
from unittest.mock import patch
import pytest
from test_financing import CITY, PRODUCT, AT, assess
from backend.src.scoring import recommend_financing
from backend.src.scoring.rules import score_company

MEDIUM = CITY | dict(monthlyRevenue=10000000, monthlyExpenses=9500000,
                     existingPayments=300000, registrationDate="2026-10-01")


def test_review_offer_and_reduction_follow_stricter_policy():
    direct = assess(MEDIUM, amount=100000)
    assert 50 <= direct["scoring"]["score"] < 70
    assert direct["assessment"] == "manual_review"
    assert direct["policyPasses"] and direct["reviewRequired"]
    assert not direct["eligible"]
    assert direct["requiredCoverage"] == 1.5
    result = assess(MEDIUM, amount=800000)
    assert not result["policyPasses"]
    alternative = result["alternative"]
    assert alternative is not None
    assert alternative["amount"] < 800000
    assert alternative["coverage"] >= 1.5
    assert alternative["reviewRequired"] and not alternative["eligible"]
    rechecked = assess(MEDIUM, amount=alternative["amount"])
    assert rechecked["policyPasses"]
    ranked = recommend_financing(MEDIUM, [PRODUCT], purpose="goods", amount=800000,
                                term_months=24, evaluated_at=AT)
    assert not ranked["groups"]["requested"]
    assert not ranked["groups"]["reduced_amount"]
    assert any(item["offer"]["amount"] < 800000 for item in ranked["groups"]["requires_action"])


@pytest.mark.parametrize("score,review,allowed", [(49,False,False),(50,True,True),(69,True,True),(70,False,True)])
def test_policy_score_boundaries(score, review, allowed):
    base_score = score_company(CITY, evaluated_at=AT) | {"score": score}
    company = CITY | dict(monthlyRevenue=2000000, monthlyExpenses=1000000, existingPayments=0)
    with patch("backend.src.scoring.financing.score_company", return_value=base_score):
        result = assess(company, amount=100000)
    assert result["reviewRequired"] == review
    assert result["policyPasses"] == allowed
    assert result["eligible"] == (allowed and not review)


@pytest.mark.parametrize("change", [{"hasOverdue": True}, {"active": False}, {"documents": []}])
def test_review_never_bypasses_nonfinancial_restrictions(change):
    result = assess(MEDIUM | change, amount=100000)
    assert not result["policyPasses"]
    assert result["alternative"] is None


def test_review_amount_limit_and_payment_rounding():
    company = MEDIUM | dict(existingPayments=0)
    fixed_score = score_company(MEDIUM, evaluated_at=AT)
    with patch("backend.src.scoring.financing.score_company", return_value=fixed_score):
        result = assess(company, PRODUCT | {"maxAmount": 10000000}, amount=6000000)
    assert result["amountLimit"] == 5000000
    assert result["alternative"]["amount"] <= result["amountLimit"]
    assert Decimal(str(result["alternative"]["monthlyPayment"])) + Decimal("0") <= Decimal("500000") / Decimal("1.5")
