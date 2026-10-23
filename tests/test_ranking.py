import json
import unittest
from copy import deepcopy
from backend.src.scoring import recommend_financing, InputError
from test_financing import CITY, CAFE, PRODUCT, AT


def recommend(company=CAFE, products=None, **changes):
    return recommend_financing(company, products if products is not None else [PRODUCT],
                               **(dict(purpose="goods", amount=800000, term_months=24,
                                       evaluated_at=AT) | changes))


class RankingTests(unittest.TestCase):
    def test_groups_and_preference(self):
        interest = recommend()["groups"]
        payment = recommend(preference="min_payment")["groups"]
        self.assertEqual(interest["requested"][0]["offer"]["termMonths"], 24)
        self.assertEqual(interest["other_terms"][0]["offer"]["termMonths"], 12)
        self.assertEqual(payment["other_terms"][0]["offer"]["termMonths"], 36)

    def test_reduced_amount_is_not_an_original_approval(self):
        groups = recommend(CITY)["groups"]
        self.assertFalse(groups["requested"])
        self.assertFalse(groups["other_terms"])
        reduced = groups["reduced_amount"]
        self.assertGreater(len(reduced), 1)
        amounts = [x["offer"]["amount"] for x in reduced]
        self.assertEqual(amounts, sorted(amounts, reverse=True))
        for item in reduced:
            self.assertTrue(item["offer"]["eligible"])
            self.assertFalse(item["evaluation"]["eligible"])
            self.assertEqual(item["amountShortfall"], 800000 - item["offer"]["amount"])

    def test_order_is_independent_of_catalog_order_and_ties(self):
        products = [PRODUCT | {"id": "b"}, PRODUCT | {"id": "a"}]
        result = recommend(products=products)
        self.assertEqual(result, recommend(products=products[::-1]))
        self.assertEqual(result["groups"]["requested"][0]["product"]["id"], "a")
        json.dumps(result, allow_nan=False)

    def test_blocked_and_missing_documents_never_recommended(self):
        for company in (CAFE | {"hasOverdue": True}, CAFE | {"documents": []}):
            groups = recommend(company)["groups"]
            for key in ("requested", "other_terms", "reduced_amount"):
                self.assertFalse(groups[key])
            self.assertTrue(groups["requires_action"])

    def test_empty_catalog_validation_and_mismatch(self):
        self.assertTrue(all(not v for v in recommend(products=[])["groups"].values()))
        with self.assertRaises(InputError):
            recommend(products=[], amount=0)
        with self.assertRaises(InputError):
            recommend(preference="magic")
        with self.assertRaises(InputError):
            recommend(products=[PRODUCT, PRODUCT])
        result = recommend(purpose="equipment")["groups"]
        self.assertEqual(len(result["unavailable"]), 1)
        self.assertFalse(result["requested"])

    def test_no_mutation_duplicate_terms_and_unsupported_requested_term(self):
        products = [deepcopy(PRODUCT) | {"terms": [12, 12, 36]}]
        before = deepcopy(products)
        result = recommend(products=products)
        self.assertEqual(products, before)
        self.assertFalse(result["groups"]["requested"])
        self.assertEqual(len(result["groups"]["other_terms"]), 2)
        result["groups"]["other_terms"][0]["product"]["terms"].append(60)
        self.assertEqual(products, before)
