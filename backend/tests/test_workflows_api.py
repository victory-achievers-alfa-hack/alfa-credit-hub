from collections.abc import Generator

import pytest
from backend.main import app
from backend.src.database import Base
from backend.src.dependency import get_db
from backend.src.seed import seed_demo_data
from backend.src.service.realtime import realtime_connections
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    with testing_session() as db:
        seed_demo_data(db)

    def override_get_db():
        with testing_session() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)
        test_client.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def login(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "123456"}
    )
    assert response.status_code == 200, response.text
    return response.json()["accessToken"]


@pytest.fixture
def published_realtime_events(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    events: list[dict] = []

    async def capture(event: dict) -> None:
        events.append(event)

    monkeypatch.setattr(realtime_connections, "publish", capture)
    return events


def assert_application_update(events: list[dict], response) -> None:
    application = response.json()
    application_events = [
        event for event in events if event["type"] == "application.updated"
    ]
    assert application_events == [
        {
            "type": "application.updated",
            "companyId": application["companyId"],
            "applicationId": application["id"],
            "status": application["status"],
            "payload": {"application": application},
        }
    ]


def test_authentication_login_me_and_unauthorized(client: TestClient) -> None:
    assert client.get("/api/v1/me").status_code == 401

    token = login(client, "client@demo.ru")
    response = client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, response.text
    assert response.json()["email"] == "client@demo.ru"


def test_client_isolation_and_bank_role(client: TestClient) -> None:
    token = login(client, "client@demo.ru")
    headers = {"Authorization": f"Bearer {token}"}

    foreign_application = client.get(
        "/api/v1/applications/APP-2026-002", headers=headers
    )
    assert foreign_application.status_code == 404

    forbidden = client.get("/api/v1/bank/applications", headers=headers)
    assert forbidden.status_code == 403


def test_decimal_fields_are_json_numbers(client: TestClient) -> None:
    token = login(client, "client@demo.ru")
    headers = {"Authorization": f"Bearer {token}"}

    application = client.get("/api/v1/applications/APP-2026-001", headers=headers)
    assert application.status_code == 200, application.text
    application_data = application.json()
    assert type(application_data["coverage"]) is float
    assert type(application_data["requestedAmount"]) is float
    assert type(application_data["offer"]["amount"]) is float

    company = client.get("/api/v1/companies/me", headers=headers)
    assert company.status_code == 200, company.text
    assert type(company.json()["monthlyRevenue"]) is float

    catalog = client.get("/api/v1/credit-products")
    assert catalog.status_code == 200, catalog.text
    assert type(catalog.json()[0]["minAmount"]) is float


def test_seed_offer_comment_is_preserved_in_event_history(
    client: TestClient,
) -> None:
    token = login(client, "client@demo.ru")
    headers = {"Authorization": f"Bearer {token}"}

    for _ in range(2):
        response = client.get("/api/v1/applications/APP-2026-001", headers=headers)
        assert response.status_code == 200, response.text
        application = response.json()
        offer_event = next(
            event for event in application["events"] if event["id"] == "EV-002"
        )
        assert offer_event["description"] == application["offer"]["reason"]


def test_http_notifications_match_realtime_payload_fields(client: TestClient) -> None:
    token = login(client, "client@demo.ru")
    headers = {"Authorization": f"Bearer {token}"}

    listed = client.get("/api/v1/notifications", headers=headers)
    assert listed.status_code == 200, listed.text
    notification = listed.json()["items"][0]
    assert set(notification) == {
        "id",
        "companyId",
        "applicationId",
        "title",
        "message",
        "tone",
        "createdAt",
        "read",
    }
    assert notification["companyId"] == "city"
    assert notification["applicationId"] == "APP-2026-001"
    assert notification["tone"] == "warning"
    assert notification["read"] is False

    marked = client.post(
        f"/api/v1/notifications/{notification['id']}/read", headers=headers
    )
    assert marked.status_code == 200, marked.text
    assert set(marked.json()) == set(notification)
    assert marked.json()["read"] is True


def test_zernya_application_approval_and_disbursement(
    client: TestClient,
    published_realtime_events: list[dict],
) -> None:
    client_token = login(client, "cafe@demo.ru")
    bank_token = login(client, "bank@demo.ru")
    client_headers = {"Authorization": f"Bearer {client_token}"}
    bank_headers = {"Authorization": f"Bearer {bank_token}"}
    application_id = "APP-2026-002"

    decision = client.post(
        f"/api/v1/bank/applications/{application_id}/decision",
        headers=bank_headers,
        json={"kind": "approve"},
    )
    assert decision.status_code == 200, decision.text
    assert decision.json()["status"] == "offer"
    assert_application_update(published_realtime_events, decision)
    published_realtime_events.clear()

    for endpoint, expected_status in (
        ("accept", "sign"),
        ("sign", "ready"),
        ("disburse", "disbursed"),
    ):
        response = client.post(
            f"/api/v1/applications/{application_id}/{endpoint}",
            headers=client_headers,
            json={"accepted": True} if endpoint == "accept" else None,
        )
        assert response.status_code == 200, response.text
        assert response.json()["status"] == expected_status
        assert_application_update(published_realtime_events, response)
        published_realtime_events.clear()


def test_gorod_alternative_offer_and_decline(
    client: TestClient,
    published_realtime_events: list[dict],
) -> None:
    client_token = login(client, "client@demo.ru")
    bank_token = login(client, "bank@demo.ru")
    client_headers = {"Authorization": f"Bearer {client_token}"}
    bank_headers = {"Authorization": f"Bearer {bank_token}"}

    created = client.post(
        "/api/v1/applications",
        headers=client_headers,
        json={
            "productId": "working-capital",
            "purpose": "goods",
            "amount": 800000,
            "termMonths": 24,
        },
    )
    assert created.status_code == 200, created.text
    application_id = created.json()["id"]
    assert created.json()["status"] == "review"
    assert_application_update(published_realtime_events, created)
    published_realtime_events.clear()

    offer = client.post(
        f"/api/v1/bank/applications/{application_id}/decision",
        headers=bank_headers,
        json={
            "kind": "alternative",
            "amount": 150000,
            "termMonths": 24,
            "rate": 24,
            "comment": "Сумма скорректирована по коэффициенту покрытия.",
        },
    )
    assert offer.status_code == 200, offer.text
    assert offer.json()["status"] == "offer"
    assert float(offer.json()["offer"]["amount"]) == 150000
    assert_application_update(published_realtime_events, offer)
    published_realtime_events.clear()

    declined = client.post(
        f"/api/v1/applications/{application_id}/accept",
        headers=client_headers,
        json={"accepted": False},
    )
    assert declined.status_code == 200, declined.text
    assert declined.json()["status"] == "rejected"
    assert_application_update(published_realtime_events, declined)


def test_vector_need_info_review_rejection_and_invalid_transition(
    client: TestClient,
    published_realtime_events: list[dict],
) -> None:
    client_token = login(client, "vector@demo.ru")
    bank_token = login(client, "bank@demo.ru")
    client_headers = {"Authorization": f"Bearer {client_token}"}
    bank_headers = {"Authorization": f"Bearer {bank_token}"}
    application_id = "APP-2026-003"
    decision_url = f"/api/v1/bank/applications/{application_id}/decision"

    bank_info_comment = "Уточните сведения о задолженности."
    client_info_comment = "Сведения предоставлены."
    rejection_comment = "Высокая долговая нагрузка."
    need_info = client.post(
        decision_url,
        headers=bank_headers,
        json={"kind": "need_info", "comment": bank_info_comment},
    )
    assert need_info.status_code == 200, need_info.text
    assert need_info.json()["status"] == "need_info"
    assert_application_update(published_realtime_events, need_info)
    published_realtime_events.clear()

    returned = client.post(
        f"/api/v1/applications/{application_id}/additional-info",
        headers=client_headers,
        json={"comment": client_info_comment},
    )
    assert returned.status_code == 200, returned.text
    assert returned.json()["status"] == "review"
    assert_application_update(published_realtime_events, returned)
    published_realtime_events.clear()

    rejected = client.post(
        decision_url,
        headers=bank_headers,
        json={"kind": "reject", "comment": rejection_comment},
    )
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["status"] == "rejected"
    assert_application_update(published_realtime_events, rejected)

    for _ in range(2):
        reloaded = client.get(
            f"/api/v1/applications/{application_id}", headers=client_headers
        )
        assert reloaded.status_code == 200, reloaded.text
        descriptions = {
            event["description"] for event in reloaded.json()["events"]
        }
        assert {
            bank_info_comment,
            client_info_comment,
            rejection_comment,
        } <= descriptions

    published_realtime_events.clear()
    invalid_transition = client.post(
        f"/api/v1/applications/{application_id}/accept",
        headers=client_headers,
        json={"accepted": True},
    )
    assert invalid_transition.status_code == 409
    assert invalid_transition.json()["code"] == "INVALID_STATUS_TRANSITION"
    assert published_realtime_events == []


def test_cookie_logout(client: TestClient) -> None:
    login(client, "cafe@demo.ru")
    assert client.get("/api/v1/me").status_code == 200
    assert client.post("/api/v1/auth/logout").status_code == 204
    assert client.get("/api/v1/me").status_code == 401


@pytest.mark.parametrize("kind", ["approve", "alternative"])
def test_bank_cannot_bypass_current_eligibility(client: TestClient, kind: str) -> None:
    token = login(client, "bank@demo.ru")
    headers = {"Authorization": f"Bearer {token}"}
    url = "/api/v1/bank/applications/APP-2026-003"
    before = client.get(url, headers=headers).json()
    payload = {"kind": kind}
    if kind == "alternative":
        payload.update(amount=100000, termMonths=24, rate=24, comment="Проверка альтернативы")
    response = client.post(url + "/decision", headers=headers, json=payload)
    assert response.status_code == 409, response.text
    assert response.json()["code"] == "OFFER_NOT_ELIGIBLE"
    after = client.get(url, headers=headers).json()
    assert after == before


def test_profile_score_is_calculated_from_current_data(client: TestClient) -> None:
    from backend.src.models import Company
    from sqlalchemy import select
    session_generator = app.dependency_overrides[get_db]()
    db = next(session_generator)
    company = db.scalar(select(Company).where(Company.id == "city"))
    company.scoring_score = 1
    db.commit()
    try:
        login(client, "client@demo.ru")
        response = client.get("/api/v1/companies/me")
        assert response.status_code == 200, response.text
        assert response.json()["scoringScore"] != 1
    finally:
        session_generator.close()


def test_seed_application_score_matches_current_company_score(client: TestClient) -> None:
    client_token = login(client, "vector@demo.ru")
    profile = client.get(
        "/api/v1/companies/me",
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert profile.status_code == 200, profile.text

    bank_token = login(client, "bank@demo.ru")
    application = client.get(
        "/api/v1/bank/applications/APP-2026-003",
        headers={"Authorization": f"Bearer {bank_token}"},
    )
    assert application.status_code == 200, application.text
    assert profile.json()["scoringScore"] == 20
    assert application.json()["application"]["scoring"]["score"] == 20


def test_recommendation_audit_to_new_application_disbursement(client: TestClient) -> None:
    from backend.src.models import RecommendationAudit
    token = login(client, "cafe@demo.ru")
    headers = {"Authorization": f"Bearer {token}"}
    calculated = client.post("/api/v1/recommendations", headers=headers, json={
        "purpose": "goods", "amount": 800000, "termMonths": 24,
        "preference": "min_interest",
    })
    assert calculated.status_code == 200, calculated.text
    data = calculated.json()
    session_generator = app.dependency_overrides[get_db]()
    db = next(session_generator)
    try:
        audit = db.get(RecommendationAudit, data["evaluationId"])
        assert audit is not None
        assert audit.record["result"] == data
    finally:
        session_generator.close()
    choice = data["groups"]["requested"][0]
    created = client.post("/api/v1/applications", headers=headers, json={
        "productId": choice["product"]["id"], "purpose": "goods",
        "amount": choice["offer"]["amount"], "termMonths": choice["offer"]["termMonths"],
    })
    assert created.status_code == 200, created.text
    application = created.json()
    assert application["scoring"]["modelVersion"] == "rules-v1.0.0"
    assert application["stress"]["amount"] == application["requestedAmount"]
    assert not any(action["code"] == "SUBMIT_APPLICATION" for action in application["actions"])
    assert [r["revenueDeclinePercent"] for r in application["stress"]["scenarios"]] == [0, 10, 20, 30]
    application_id = application["id"]
    bank_token = login(client, "bank@demo.ru")
    approved = client.post(f"/api/v1/bank/applications/{application_id}/decision",
        headers={"Authorization": f"Bearer {bank_token}"}, json={"kind": "approve"})
    assert approved.status_code == 200, approved.text
    assert approved.json()["actions"] == []
    for endpoint, expected in (("accept", "sign"), ("sign", "ready"), ("disburse", "disbursed")):
        response = client.post(f"/api/v1/applications/{application_id}/{endpoint}",
            headers=headers, json={"accepted": True} if endpoint == "accept" else None)
        assert response.status_code == 200, response.text
        assert response.json()["status"] == expected


def test_medium_score_bank_review_requires_reason_and_persists_audit(client: TestClient) -> None:
    from backend.src.models import Company, RecommendationAudit
    from datetime import date
    session_generator = app.dependency_overrides[get_db]()
    db = next(session_generator)
    company = db.get(Company, "city")
    company.registration_date = date.today().replace(day=1)
    company.monthly_revenue = 10000000
    company.monthly_expenses = 9500000
    company.current_monthly_debt_payment = 300000
    db.commit()
    try:
        token = login(client, "client@demo.ru")
        created = client.post("/api/v1/applications", headers={"Authorization": f"Bearer {token}"},
            json={"productId": "working-capital", "purpose": "goods", "amount": 100000, "termMonths": 24})
        assert created.status_code == 200, created.text
        application_id = created.json()["id"]
        assert 50 <= created.json()["scoring"]["score"] < 70
        bank_token = login(client, "bank@demo.ru")
        headers = {"Authorization": f"Bearer {bank_token}"}
        url = f"/api/v1/bank/applications/{application_id}/decision"
        denied = client.post(url, headers=headers, json={"kind": "approve", "comment": " "})
        assert denied.status_code == 409, denied.text
        assert denied.json()["code"] == "REVIEW_JUSTIFICATION_REQUIRED"
        approved = client.post(url, headers=headers, json={"kind": "approve",
            "comment": "Проверены документы и устойчивость покрытия для ограниченной суммы."})
        assert approved.status_code == 200, approved.text
        from sqlalchemy import select
        records = db.scalars(select(RecommendationAudit)).all()
        decision_audit = next(r for r in records if r.record.get("applicationId") == application_id)
        assert decision_audit.record["result"]["reviewRequired"]
        assert decision_audit.record["result"]["policyPasses"]
        assert decision_audit.record["result"]["stress"]["coverageThreshold"] == 1.5
        assert decision_audit.record["result"]["policyVersion"] == "financing-v1.3.0"
    finally:
        session_generator.close()


@pytest.mark.parametrize("change", [{"has_overdue": True}, {"monthly_expenses": 1200000}])
def test_bank_rechecks_changed_sources_and_preserves_submission_snapshot(client: TestClient, change: dict) -> None:
    from backend.src.models import Company, RecommendationAudit
    from sqlalchemy import select
    client_token = login(client, "cafe@demo.ru")
    created = client.post("/api/v1/applications", headers={"Authorization": f"Bearer {client_token}"},
        json={"productId": "working-capital", "purpose": "goods", "amount": 100000, "termMonths": 24})
    assert created.status_code == 200, created.text
    submitted = created.json()
    session_generator = app.dependency_overrides[get_db]()
    db = next(session_generator)
    try:
        company = db.get(Company, "cafe")
        for field, value in change.items():
            setattr(company, field, value)
        db.commit()
        bank_token = login(client, "bank@demo.ru")
        headers = {"Authorization": f"Bearer {bank_token}"}
        url = f"/api/v1/bank/applications/{submitted['id']}"
        for payload in ({"kind": "approve"}, {"kind": "alternative", "amount": 100000, "termMonths": 36, "rate": 24, "comment": "Изменение срока не должно обходить текущие ограничения."}):
            denied = client.post(url + "/decision", headers=headers, json=payload)
            assert denied.status_code == 409, denied.text
            assert denied.json()["code"] == "OFFER_NOT_ELIGIBLE"
        after = client.get(url, headers=headers).json()["application"]
        assert after["status"] == "review"
        assert after["scoring"] == submitted["scoring"]
        assert after["stress"] == submitted["stress"]
        assert after["events"] == submitted["events"]
        assert not db.scalars(select(RecommendationAudit)).all()
    finally:
        session_generator.close()
