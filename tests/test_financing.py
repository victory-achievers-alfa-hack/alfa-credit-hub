import json
import math
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from random import Random

from backend.src.scoring import InputError, assess_financing, loan_quote

AT = datetime(2026, 10, 23, tzinfo=timezone.utc)
DOCS = [{"id": key, "status": "ready"} for key in ("registry", "statement", "reporting", "bki")]
CITY = dict(registrationDate="2019-03-18", monthlyRevenue=900000,
            monthlyExpenses=740000, existingPayments=120000,
            hasOverdue=False, active=True, documents=DOCS)
CAFE = CITY | dict(registrationDate="2018-07-04", monthlyRevenue=1200000,
                   monthlyExpenses=850000, existingPayments=70000)
PRODUCT = dict(id="working-capital", name="Оборотный", minAmount=100000,
               maxAmount=3000000, rate=24, terms=[12, 24, 36], purposes=["goods", "cash_gap"])


def assess(company=None, product=None, **kwargs):
    return assess_financing(company if company is not None else CITY,
                            product if product is not None else PRODUCT,
                            **(dict(purpose="goods", amount=800000, term_months=24,
                                    evaluated_at=AT) | kwargs))


class FinancingTests(unittest.TestCase):
    def test_independent_payment_examples(self):
        # Independent closed-form float calculation, away from cent boundaries.
        for principal, annual, term in ((800000, 24, 24), (100000, 12, 12),
                                        (5000000, 22, 60), (123456.78, 29, 36)):
            r = annual / 1200
            expected = math.ceil(principal * r * (1 + r)**term / ((1 + r)**term - 1) * 100) / 100
            with self.subTest(principal=principal):
                self.assertEqual(loan_quote(principal, annual, term)["monthlyPayment"], expected)

    def test_zero_rate_and_final_payment(self):
        result = loan_quote(100, 0, 3)
        self.assertEqual(result["monthlyPayment"], 33.34)
        self.assertEqual(result["lastPayment"], 33.32)
        self.assertEqual(result["totalRepayment"], 100)
        self.assertEqual(result["interestAmount"], 0)
        result = loan_quote(100, 12, 1)
        self.assertEqual(result["monthlyPayment"], 101)
        self.assertEqual(result["lastPayment"], 101)

    def test_repayment_accounting(self):
        rng = Random(123)
        for _ in range(200):
            amount, rate, term = rng.randint(10000, 5000000), rng.randint(0, 100), rng.randint(1, 120)
            quote = loan_quote(amount, rate, term)
            payment = Decimal(str(quote["monthlyPayment"]))
            last = Decimal(str(quote["lastPayment"]))
            total = Decimal(str(quote["totalRepayment"]))
            self.assertLessEqual(last, payment)
            self.assertGreaterEqual(last, 0)
            self.assertEqual(payment * (term - 1) + last, total)
            self.assertEqual(total - amount, Decimal(str(quote["interestAmount"])))
            # Independent float recurrence: final balance must be within half a kopeck.
            balance = float(amount)
            for _month in range(term - 1):
                balance = balance * (1 + rate / 1200) - float(payment)
            balance = balance * (1 + rate / 1200) - float(last)
            self.assertLessEqual(abs(balance), 0.00501)

    def test_demo_is_reproducible_and_json_serializable(self):
        from examples.financing_demo import demo_results
        first = demo_results()
        self.assertEqual(first, demo_results())
        self.assertEqual(len(first), 4)
        json.dumps(first, allow_nan=False)

    def test_city_alternative_passes_full_policy(self):
        result = assess()
        self.assertEqual(result["assessment"], "alternative")
        self.assertFalse(result["eligible"])
        self.assertEqual(result["recommendedAmount"], 150000)
        self.assertLess(result["coverage"], 1.25)
        alternative = assess(amount=result["recommendedAmount"])
        self.assertTrue(alternative["eligible"])
        self.assertGreaterEqual(alternative["coverage"], 1.25)
        self.assertFalse(assess(amount=160000)["eligible"])

    def test_cafe_eligible_vector_blocked(self):
        self.assertTrue(assess(CAFE)["eligible"])
        vector = CITY | dict(monthlyRevenue=500000, monthlyExpenses=490000,
                             existingPayments=90000, hasOverdue=True, registrationDate="2025-05-12")
        self.assertEqual(assess(vector)["assessment"], "blocked")
        self.assertIsNone(assess(vector)["alternative"])

    def test_hard_guards_override_high_score(self):
        for change, code in (({"hasOverdue": True}, "CURRENT_OVERDUE"),
                             ({"active": False}, "INACTIVE_COMPANY")):
            result = assess(CAFE | change)
            self.assertGreaterEqual(result["scoring"]["score"], 70)
            self.assertEqual(result["assessment"], "blocked")
            self.assertIsNone(result["recommendedAmount"])
            self.assertIn(code, [r["code"] for r in result["reasons"]])

    def test_incomplete_documents_never_pass(self):
        for documents in (None, [], DOCS[:-1], [d | {"status": "attention"} for d in DOCS]):
            result = assess(CAFE | {"documents": documents})
            self.assertEqual(result["assessment"], "need_info")
            self.assertFalse(result["eligible"])
            self.assertIsNone(result["alternative"])

    def test_product_limits_and_alternative_cap(self):
        for kwargs in ({"purpose": "equipment"}, {"term_months": 60}, {"amount": 90000}):
            result = assess(CAFE, **kwargs)
            self.assertEqual(result["assessment"], "unavailable")
            self.assertIsNone(result["alternative"])
        result = assess(CAFE, amount=4000000)
        self.assertEqual(result["recommendedAmount"], 3000000)
        self.assertEqual(result["assessment"], "alternative")

    def test_low_score_requires_review_even_when_new_payment_fits(self):
        company = CITY | dict(monthlyRevenue=10000000, monthlyExpenses=9500000,
                              existingPayments=450000, registrationDate="2026-10-01")
        result = assess(company, amount=100000)
        self.assertLess(result["scoring"]["score"], 70)
        self.assertEqual(result["assessment"], "manual_review")

    def test_exact_threshold_not_rounded_display(self):
        product = PRODUCT | dict(rate=0, minAmount=100, terms=[1])
        company = CAFE | dict(monthlyRevenue=200, monthlyExpenses=75, existingPayments=0)
        self.assertTrue(assess(company, product, amount=100, term_months=1)["eligible"])
        result = assess(company | {"monthlyExpenses": 75.01}, product, amount=100, term_months=1)
        self.assertFalse(result["eligible"])
        self.assertEqual(round(result["coverage"], 2), 1.25)

    def test_no_available_amount_and_non_grid_minimum(self):
        company = CAFE | dict(monthlyRevenue=1000, monthlyExpenses=0, existingPayments=0)
        self.assertEqual(assess(company)["assessment"], "unavailable")
        company = CAFE | dict(monthlyRevenue=200000, monthlyExpenses=0, existingPayments=49000)
        product = PRODUCT | dict(minAmount=105000, rate=0, terms=[1])
        result = assess(company, product, amount=120000, term_months=1)
        self.assertEqual(result["recommendedAmount"], 110000)
        result = assess(company | {"existingPayments": 54000}, product, amount=120000, term_months=1)
        self.assertEqual(result["recommendedAmount"], 105000)

    def test_invalid_inputs(self):
        for amount, rate, term in ((0, 24, 12), (-1, 24, 12), (100, -1, 12),
                                   (100, 101, 12), (100, 24, 0), (100, 24, True),
                                   (100, 24, 12.0), (100, "NaN", 12), (100, 24, 121)):
            with self.subTest(amount=amount, rate=rate, term=term), self.assertRaises(InputError):
                loan_quote(amount, rate, term)
        for company in (CITY | {"active": None}, CITY | {"documents": DOCS + DOCS},
                        CITY | {"documents": [{"id": "bki", "status": "unknown"}]}):
            with self.assertRaises(InputError):
                assess(company)

    def test_portfolio_invariants_and_no_mutation(self):
        rng = Random(66)
        original = json.dumps([CITY, PRODUCT], sort_keys=True)
        for _ in range(150):
            revenue = rng.randint(100000, 5000000)
            company = CITY | dict(monthlyRevenue=revenue, monthlyExpenses=rng.randint(0, revenue),
                                  existingPayments=rng.randint(0, revenue // 2))
            result = assess(company)
            json.dumps(result, allow_nan=False)
            alternative = result["alternative"]
            if alternative:
                self.assertTrue(assess(company, amount=alternative["amount"])["eligible"])
                self.assertLess(alternative["amount"], 800000)
                # Independent maximality check on the finite proposal grid.
                allowed = [a for a in range(100000, 800001, 10000)
                           if Decimal(str(loan_quote(a, 24, 24)["monthlyPayment"]))
                           + company["existingPayments"] <=
                           Decimal(company["monthlyRevenue"] - company["monthlyExpenses"]) / Decimal("1.25")]
                self.assertEqual(alternative["amount"], max(allowed))
            worse = assess(company | {"existingPayments": company["existingPayments"] + 100000})
            self.assertFalse(worse["eligible"] and not result["eligible"])
        self.assertEqual(json.dumps([CITY, PRODUCT], sort_keys=True), original)


if __name__ == "__main__":
    unittest.main()
