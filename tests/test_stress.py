import json
import unittest
from copy import deepcopy
from backend.src.scoring import stress_financing, assess_financing
from test_financing import CITY, CAFE, PRODUCT, AT


def stress(company=CAFE, product=PRODUCT, **changes):
    return stress_financing(company, product, **(dict(purpose="goods", amount=800000,
                            term_months=24, evaluated_at=AT) | changes))


class StressTests(unittest.TestCase):
    def test_baseline_and_fixed_request(self):
        result = stress()
        baseline = assess_financing(CAFE, PRODUCT, purpose="goods", amount=800000,
                                    term_months=24, evaluated_at=AT)
        self.assertEqual(result["scenarios"][0]["evaluation"], baseline)
        for scenario in result["scenarios"]:
            self.assertEqual(scenario["evaluation"]["amount"], 800000)
            self.assertEqual(scenario["evaluation"]["monthlyPayment"], baseline["monthlyPayment"])
        self.assertEqual(result["requiredMonthlyRevenue"], 990371.1)
        self.assertAlmostEqual(result["maxRevenueDeclinePercent"], 17.469075)
        self.assertEqual([s["coveragePasses"] for s in result["scenarios"]], [True, True, False, False])

    def test_failing_baseline_and_zero_revenue(self):
        result = stress(CITY)
        self.assertIsNone(result["maxRevenueDeclinePercent"])
        self.assertLess(result["revenueHeadroom"], 0)
        self.assertEqual(result["coverageStatus"], "below_threshold")
        result = stress(CITY | {"monthlyRevenue": 0})
        self.assertIsNone(result["maxRevenueDeclinePercent"])
        json.dumps(result, allow_nan=False)

    def test_exact_threshold_and_other_blockers(self):
        product = PRODUCT | dict(rate=0, terms=[1], minAmount=100)
        company = CAFE | dict(monthlyRevenue=200, monthlyExpenses=75, existingPayments=0)
        result = stress(company, product, amount=100, term_months=1)
        self.assertEqual(result["maxRevenueDeclinePercent"], 0)
        self.assertTrue(result["scenarios"][0]["coveragePasses"])
        result = stress(CAFE | {"hasOverdue": True})
        self.assertTrue(result["scenarios"][0]["coveragePasses"])
        self.assertFalse(result["scenarios"][0]["evaluation"]["eligible"])

    def test_monotonicity_reproducibility_no_mutation(self):
        company = deepcopy(CAFE)
        before = deepcopy(company)
        result = stress(company)
        self.assertEqual(result, stress(company))
        self.assertEqual(company, before)
        coverages = [s["evaluation"]["coverage"] for s in result["scenarios"]]
        self.assertEqual(coverages, sorted(coverages, reverse=True))
        scores = [s["evaluation"]["scoring"]["score"] for s in result["scenarios"]]
        self.assertEqual(scores, sorted(scores, reverse=True))
        json.dumps(result, allow_nan=False)


class StressReviewIntegrationTests(unittest.TestCase):
    def test_review_uses_initial_stricter_coverage_threshold(self):
        from test_review_policy import MEDIUM
        result = stress(MEDIUM, amount=100000)
        baseline = result["scenarios"][0]["evaluation"]
        self.assertTrue(baseline["reviewRequired"])
        self.assertEqual(result["coverageThreshold"], 1.5)
        from decimal import Decimal
        expected = Decimal(str(MEDIUM["monthlyExpenses"])) + Decimal("1.5") * (Decimal(str(MEDIUM["existingPayments"])) + Decimal(str(baseline["monthlyPayment"])))
        self.assertEqual(result["requiredMonthlyRevenue"], float(expected))
        self.assertTrue(result["scenarios"][0]["coveragePasses"])
        self.assertFalse(result["scenarios"][1]["coveragePasses"])

    def test_compact_stress_matches_detailed_calculation(self):
        from backend.src.scoring.stress import stress_summary
        summary = stress_summary(CAFE, PRODUCT, purpose="goods", amount=800000,
                                 term_months=24, evaluated_at=AT)
        detailed = stress()
        for compact, full in zip(summary["scenarios"], detailed["scenarios"]):
            self.assertEqual(compact["coverage"], full["evaluation"]["coverage"])
            self.assertEqual(compact["policyPasses"], full["evaluation"]["policyPasses"])
        self.assertEqual(summary["amount"], 800000)
        self.assertEqual(summary["termMonths"], 24)
        json.dumps(summary, allow_nan=False)

    def test_recommendation_stress_is_for_selected_alternative(self):
        from backend.src.scoring import recommend_financing
        ranked = recommend_financing(CITY, [PRODUCT], purpose="goods", amount=800000,
                                    term_months=24, evaluated_at=AT)
        for item in ranked["groups"]["reduced_amount"]:
            self.assertEqual(item["stress"]["amount"], item["offer"]["amount"])
            self.assertEqual(item["stress"]["termMonths"], item["offer"]["termMonths"])
            self.assertEqual(item["stress"]["scenarios"][0]["coverage"], item["offer"]["coverage"])
