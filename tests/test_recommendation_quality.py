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


def ranked_products(products, company=CAFE, **changes):
    return recommend_financing(company, products, **(dict(purpose='goods', amount=800000,
        term_months=24, evaluated_at=AT) | changes))


def test_single_offer_never_claims_comparative_superiority():
    result = ranked_products([PRODUCT | {'terms': [24]}])
    item = result['groups']['requested'][0]
    assert item['comparisonCount'] == 1
    assert item['comparisonAmount'] == 800000
    assert item['highlights'] == []


def test_identical_offers_have_no_artificial_winner():
    first = PRODUCT | {'terms': [24]}
    result = ranked_products([first, first | {'id': 'equal'}])
    assert len(result['groups']['requested']) == 2
    assert all(i['comparisonCount'] == 2 and not i['highlights'] for i in result['groups']['requested'])


def test_smaller_principal_is_not_compared_by_absolute_interest():
    result = ranked_products([PRODUCT | {'terms': [24]}, PRODUCT | {'id': 'higher-rate', 'rate': 29, 'terms': [24]}],
                             company=CITY, amount=5000000)
    items = result['groups']['reduced_amount']
    assert len(items) == 2
    assert items[0]['offer']['amount'] > items[1]['offer']['amount']
    assert all(i['comparisonCount'] == 1 and not i['highlights'] for i in items)


def test_equal_best_offers_can_share_a_meaningful_highlight():
    first = PRODUCT | {'terms': [24]}
    result = ranked_products([first, first | {'id': 'equal'}, first | {'id': 'expensive', 'rate': 40}])
    items = {i['product']['id']: i for i in result['groups']['requested']}
    assert items[PRODUCT['id']]['highlights'] == items['equal']['highlights']
    assert items[PRODUCT['id']]['highlights']
    assert not items['expensive']['highlights']
    assert all(i['comparisonCount'] == 3 for i in items.values())


def test_catalog_input_order_does_not_change_rank_or_comparisons():
    from itertools import permutations
    products = [PRODUCT, PRODUCT | {'id': 'same-rate'}, PRODUCT | {'id': 'expensive', 'rate': 40}]
    baseline = ranked_products(products)
    for ordered in permutations(products):
        assert ranked_products(list(ordered)) == baseline
