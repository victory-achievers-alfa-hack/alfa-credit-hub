import json
import unittest
from datetime import datetime, timezone
from random import Random

from backend.src.scoring import InputError, score_company


AT = datetime(2026, 10, 23, tzinfo=timezone.utc)
BASE = dict(registrationDate="2020-01-01", monthlyRevenue=900000,
            monthlyExpenses=740000, existingPayments=120000, hasOverdue=False)


def score(**changes):
    return score_company(BASE | changes, evaluated_at=AT)


class ScoringTests(unittest.TestCase):
    def test_control_example_and_explanation(self):
        result = score()
        self.assertEqual(result["score"], 85)
        self.assertEqual([f["points"] for f in result["factors"]], [30, 18, 22, 15])
        self.assertEqual(result["riskLevel"], "low")
        self.assertIsNone(result["eventProbability"])

    def test_reproducible_and_ignores_old_score(self):
        self.assertEqual(score(scoringScore=0), score(scoringScore=100))
        self.assertEqual(score(), score())
        self.assertEqual(score()["calculatedAt"], "2026-10-23T00:00:00Z")

    def test_invalid_data_does_not_become_zero(self):
        for field in ("monthlyRevenue", "monthlyExpenses", "existingPayments"):
            for bad in (None, True, -1, float("nan"), float("inf"), "x", "0.001", 10**13):
                with self.subTest(field=field, bad=bad):
                    with self.assertRaises(InputError) as error:
                        score(**{field: bad})
                    self.assertEqual(error.exception.field, field)
        for field in BASE:
            data = BASE.copy()
            del data[field]
            with self.subTest(missing=field), self.assertRaises(InputError):
                score_company(data, evaluated_at=AT)

    def test_date_and_boolean_validation(self):
        for value in ("2027-01-01", "2026-02-30", "20260101", "2026-W01-1", 20200101):
            with self.subTest(value=value), self.assertRaises(InputError):
                score(registrationDate=value)
        for value in (0, 1, "false", None):
            with self.subTest(value=value), self.assertRaises(InputError):
                score(hasOverdue=value)
        with self.assertRaises(InputError):
            score_company(BASE, evaluated_at=datetime(2026, 10, 23))

    def test_age_boundaries(self):
        for registered, expected in (("2023-10-23", 15), ("2023-10-24", 10),
                                     ("2025-10-23", 10), ("2025-10-24", 5),
                                     ("2026-04-23", 5), ("2026-04-24", 0)):
            with self.subTest(registered=registered):
                self.assertEqual(score(registrationDate=registered)["factors"][3]["points"], expected)

    def test_margin_and_coverage_boundaries(self):
        for expenses, expected in ((80, 25), (80.01, 18), (90, 18), (90.01, 10), (100, 0)):
            self.assertEqual(score(monthlyRevenue=100, monthlyExpenses=expenses)["factors"][1]["points"], expected)
        for debt, expected in ((50, 30), (50.01, 22), (80, 22), (80.01, 10), (100, 10), (100.01, 0)):
            self.assertEqual(score(monthlyRevenue=200, monthlyExpenses=100, existingPayments=debt)["factors"][2]["points"], expected)

    def test_no_debt_and_no_income_are_not_infinite_or_healthy(self):
        result = score(monthlyRevenue=0, monthlyExpenses=0, existingPayments=0)
        self.assertEqual(result["score"], 45)
        self.assertEqual(result["riskLevel"], "high")
        json.dumps(result, allow_nan=False)
        self.assertEqual(score(existingPayments=0)["factors"][2]["points"], 30)

    def test_financial_monotonicity_and_bounds(self):
        rng = Random(42)
        for _ in range(500):
            data = dict(monthlyRevenue=rng.randint(0, 1000000),
                        monthlyExpenses=rng.randint(0, 1000000),
                        existingPayments=rng.randint(0, 100000))
            initial = score(**data)
            value = initial["score"]
            self.assertTrue(0 <= value <= 100)
            self.assertEqual(value, sum(f["points"] for f in initial["factors"]))
            self.assertGreaterEqual(score(**(data | {"monthlyRevenue": data["monthlyRevenue"] + 10000}))["score"], value)
            self.assertLessEqual(score(**(data | {"monthlyExpenses": data["monthlyExpenses"] + 10000}))["score"], value)
            self.assertLessEqual(score(**(data | {"existingPayments": data["existingPayments"] + 10000}))["score"], value)
            self.assertLessEqual(score(**data, hasOverdue=True)["score"], value)


if __name__ == "__main__":
    unittest.main()
