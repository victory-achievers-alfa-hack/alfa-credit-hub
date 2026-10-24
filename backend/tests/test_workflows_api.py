from collections.abc import Generator

import pytest
from backend.main import app
from backend.src.database import Base
from backend.src.dependency import get_db
from backend.src.seed import seed_demo_data
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


def test_zernya_application_approval_and_disbursement(client: TestClient) -> None:
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


def test_gorod_alternative_offer(client: TestClient) -> None:
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


def test_vector_need_info_review_rejection_and_invalid_transition(
    client: TestClient,
) -> None:
    client_token = login(client, "vector@demo.ru")
    bank_token = login(client, "bank@demo.ru")
    client_headers = {"Authorization": f"Bearer {client_token}"}
    bank_headers = {"Authorization": f"Bearer {bank_token}"}
    application_id = "APP-2026-003"
    decision_url = f"/api/v1/bank/applications/{application_id}/decision"

    need_info = client.post(
        decision_url,
        headers=bank_headers,
        json={"kind": "need_info", "comment": "Уточните сведения о задолженности."},
    )
    assert need_info.status_code == 200, need_info.text
    assert need_info.json()["status"] == "need_info"

    returned = client.post(
        f"/api/v1/applications/{application_id}/additional-info",
        headers=client_headers,
        json={"comment": "Сведения предоставлены."},
    )
    assert returned.status_code == 200, returned.text
    assert returned.json()["status"] == "review"

    rejected = client.post(
        decision_url,
        headers=bank_headers,
        json={"kind": "reject", "comment": "Высокая долговая нагрузка."},
    )
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["status"] == "rejected"

    invalid_transition = client.post(
        f"/api/v1/applications/{application_id}/accept",
        headers=client_headers,
        json={"accepted": True},
    )
    assert invalid_transition.status_code == 409
    assert invalid_transition.json()["code"] == "INVALID_STATUS_TRANSITION"
