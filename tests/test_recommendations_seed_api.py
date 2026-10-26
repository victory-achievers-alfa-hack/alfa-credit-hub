"""Exercise production recommendation/auth routers against an isolated seeded DB."""

from decimal import Decimal
from functools import partial

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.src.api.v1 import recommendations as recommendations_api
from backend.src.api.v1.profile import router as profile_router
from backend.src.database import Base
from backend.src.dependency import get_db
from backend.src.models import RecommendationAudit
from backend.src.scoring import loan_quote
from backend.src.seed import seed_demo_data
from backend.src.service.recommendations import create_recommendations
from test_financing import AT


@pytest.fixture
def seeded_api(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    with sessions() as db:
        seed_demo_data(db)

    def override_get_db():
        with sessions() as db:
            yield db

    # Do not run backend.main's file-backed startup lifespan.
    app = FastAPI()
    app.include_router(profile_router, prefix="/api/v1")
    app.include_router(recommendations_api.router, prefix="/api/v1")
    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(
        recommendations_api,
        "create_recommendations",
        partial(create_recommendations, evaluated_at=AT),
    )
    try:
        with TestClient(app) as client:
            yield client, sessions
    finally:
        engine.dispose()


def post_recommendations(client, email, amount=800000):
    login = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "123456"}
    )
    assert login.status_code == 200, login.text
    response = client.post(
        "/api/v1/recommendations",
        headers={"Authorization": f"Bearer {login.json()['accessToken']}"},
        json={"purpose": "goods", "amount": amount, "termMonths": 24},
    )
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize(
    "email,company_id,amount,score,group_counts,status,summary_counts",
    [
        pytest.param("client@demo.ru", "city", 800000, 85, (0, 0, 4, 0, 2),
                     "alternatives_available", (0, 0, 0, 4), id="city-reduced"),
        pytest.param("cafe@demo.ru", "cafe", "800000.00", 100, (2, 3, 0, 0, 1),
                     "exact_available", (2, 0, 3, 0), id="cafe-exact"),
        pytest.param("vector@demo.ru", "vector", 800000, 20, (0, 0, 0, 5, 1),
                     "unavailable", (0, 0, 0, 0), id="vector-blocked"),
    ],
)
def test_seeded_api_groups_counters_and_original_request_audit(
    seeded_api, email, company_id, amount, score, group_counts, status, summary_counts
):
    client, sessions = seeded_api
    result = post_recommendations(client, email, amount)
    assert result["companyId"] == company_id
    assert result["calculatedAt"] == "2026-10-23T00:00:00Z"
    assert (result["requestedAmount"], result["requestedTermMonths"]) == (800000, 24)
    group_names = ("requested", "other_terms", "reduced_amount", "requires_action", "unavailable")
    assert set(result["groups"]) == set(group_names)
    assert tuple(len(result["groups"][key]) for key in group_names) == group_counts
    assert sum(map(len, result["groups"].values())) == 6
    assert [check["productId"] for check in result["requestChecks"]] == [
        "express", "investment", "working-capital"
    ]
    summary = result["requestSummary"]
    assert summary["status"] == status
    assert tuple(summary[key] for key in (
        "exactMatchCount", "exactReviewCount", "otherTermCount", "reducedAmountCount"
    )) == summary_counts
    for group, items in result["groups"].items():
        for item in items:
            assert item["group"] == group
            assert item["evaluation"]["scoring"]["score"] == score
            assert item["termChanged"] == (item["offer"]["termMonths"] != 24)
            assert item["amountShortfall"] == 800000 - item["offer"]["amount"]

    with sessions() as db:
        audit = db.get(RecommendationAudit, result["evaluationId"])
        assert audit is not None
        assert audit.company_id == company_id
        assert audit.record["result"] == result
        assert Decimal(audit.record["inputs"]["request"]["amount"]) == 800000
        assert audit.record["inputs"]["request"]["termMonths"] == 24
        assert audit.record["inputs"]["company"]["id"] == company_id
        assert len(audit.record["inputs"]["products"]) == 3


def test_city_seed_api_reductions_follow_payment_budget_and_grid(seeded_api):
    client, sessions = seeded_api
    result = post_recommendations(client, "client@demo.ru")
    with sessions() as db:
        inputs = db.get(RecommendationAudit, result["evaluationId"]).record["inputs"]
    company = inputs["company"]
    revenue = Decimal(company["monthlyRevenue"])
    expenses = Decimal(company["monthlyExpenses"])
    existing = Decimal(company["existingPayments"])
    assert (revenue, expenses, existing) == (900000, 740000, 120000)
    flow = revenue - expenses
    threshold = Decimal("1.25")
    budget = flow / threshold - existing
    assert flow == 160000
    assert budget == 8000

    reduced = result["groups"]["reduced_amount"]
    # A changed term does not double-count a reduced offer as a full-amount alternative.
    assert [(item["product"]["id"], item["offer"]["termMonths"], item["offer"]["amount"])
            for item in reduced] == [
        ("working-capital", 36, 200000),
        ("working-capital", 24, 150000),
        ("express", 24, 140000),
        ("express", 12, 80000),
    ]
    expected_payments = [7846.58, 7930.67, 7755.92, 7759.68]
    next_grid_payments = [8238.90, 8459.38, 8309.91, 8729.64]
    for item, payment, next_payment in zip(reduced, expected_payments, next_grid_payments, strict=True):
        offer, evaluation = item["offer"], item["evaluation"]
        selected = item["selectedEvaluation"]
        assert offer["monthlyPayment"] == payment
        assert Decimal(str(payment)) <= budget
        assert flow >= threshold * (existing + Decimal(str(payment)))
        assert offer["eligible"] and selected["policyPasses"]
        assert not evaluation["policyPasses"]
        assert evaluation["amount"] == 800000
        assert selected["amount"] == offer["amount"]
        assert selected["termMonths"] == offer["termMonths"]
        assert selected["alternative"] is None
        assert evaluation["constraints"]["maxNewMonthlyPayment"] == 8000
        assert {reason["code"] for reason in evaluation["reasons"]} == {
            "INSUFFICIENT_COVERAGE", "LOWER_AMOUNT_AVAILABLE"
        }
        quote = loan_quote(offer["amount"] + 10000, offer["rate"], offer["termMonths"])
        assert quote["monthlyPayment"] == next_payment
        assert Decimal(str(next_payment)) > budget

    checks = {check["productId"]: check for check in result["requestChecks"]}
    for product_id, payment in (("working-capital", Decimal("42296.88")),
                                ("express", Decimal("44319.50"))):
        check = checks[product_id]
        assert not check["policyPasses"]
        constraints = check["constraints"]
        assert constraints["totalMonthlyDebtPayment"] == float(existing + payment)
        assert constraints["monthlyCoverageShortfall"] == float(threshold * (existing + payment) - flow)
        reason = next(reason for reason in check["reasons"] if reason["code"] == "INSUFFICIENT_COVERAGE")
        assert reason["actual"] == pytest.approx(float(flow / (existing + payment)))
        assert reason["actual"] < reason["minimum"] == 1.25

    unavailable = {(item["product"]["id"], item["offer"]["termMonths"]): item
                   for item in result["groups"]["unavailable"]}
    assert set(unavailable) == {("working-capital", 12), ("investment", 24)}
    assert loan_quote(100000, 24, 12)["monthlyPayment"] == 9455.96
    assert any(reason["code"] == "NO_AFFORDABLE_AMOUNT"
               for reason in unavailable["working-capital", 12]["evaluation"]["reasons"])
    assert any(reason["code"] == "PURPOSE_MISMATCH"
               for reason in unavailable["investment", 24]["evaluation"]["reasons"])
    assert sum(item["termChanged"] for item in reduced) == 2
    assert result["requestSummary"]["otherTermCount"] == 0
    assert result["requestSummary"]["reducedAmountCount"] == 4
