from copy import deepcopy
import pytest
from test_financing import CAFE, CITY, PRODUCT, AT, DOCS, assess
from backend.src.scoring import recommend_financing


def test_missing_documents_have_precise_next_steps():
    company = CAFE | {"documents": [{"id": "doc-registry", "kind": "registry", "status": "verified"}]}
    result = assess(company)
    missing = {a["documentKind"] for a in result["actions"] if a["code"] == "PROVIDE_DOCUMENT"}
    assert missing == {"bki", "statement", "reporting"}
    assert not result["policyPasses"]
    assert not any(a["code"] == "SUBMIT_APPLICATION" for a in result["actions"])


@pytest.mark.parametrize("change,code", [({"hasOverdue": True}, "RESOLVE_OVERDUE"), ({"active": False}, "CHECK_REGISTRY")])
def test_hard_blocker_has_no_financial_workaround(change, code):
    result = assess(CITY | change)
    codes = {a["code"] for a in result["actions"]}
    assert code in codes
    assert not codes.intersection({"REDUCE_AMOUNT", "RECALCULATE_TERMS", "SUBMIT_APPLICATION", "BANK_REVIEW"})


def test_reduced_amount_explanation_matches_the_displayed_offer():
    ranked = recommend_financing(CITY, [PRODUCT], purpose="goods", amount=800000,
                                term_months=24, evaluated_at=AT)
    for item in ranked["groups"]["reduced_amount"]:
        assert not item["evaluation"]["eligible"]  # Original request remains auditable.
        selected = item["selectedEvaluation"]
        assert selected["eligible"]
        assert selected["amount"] == item["offer"]["amount"]
        assert not any(r["code"] == "INSUFFICIENT_COVERAGE" for r in selected["reasons"])
        assert any(a["code"] == "SUBMIT_APPLICATION" for a in selected["actions"])
    assert ranked["groups"]["reduced_amount"]


@pytest.mark.parametrize("preference,metric", [("min_interest","interestAmount"),("min_payment","monthlyPayment")])
def test_recommendation_quality_order_and_highlights(preference, metric):
    company = deepcopy(CAFE)
    before = deepcopy(company)
    products = [PRODUCT, PRODUCT | {"id": "expensive", "rate": 40}, PRODUCT | {"id": "wrong-purpose", "purposes": ["equipment"]}]
    ranked = recommend_financing(company, products, purpose="goods", amount=800000,
                                term_months=24, evaluated_at=AT, preference=preference)
    assert company == before
    for group in ("requested", "other_terms"):
        values = [i["offer"][metric] for i in ranked["groups"][group]]
        assert values == sorted(values)
        assert all(i["selectedEvaluation"]["policyPasses"] for i in ranked["groups"][group])
    assert all(not i["highlights"] for i in ranked["groups"]["unavailable"])
    assert all(i["product"]["id"] != "wrong-purpose" for i in ranked["groups"]["requested"])
    assert any(i["highlights"] for i in ranked["groups"]["requested"])
