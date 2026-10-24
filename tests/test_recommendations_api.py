import unittest
from copy import deepcopy
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.src.api.v1.recommendations import router, get_recommendation_actor, get_recommendation_store
from backend.src.database import Base
from backend.src.dependency import get_db
from backend.src.service.recommendations import Actor, AuthorizedSnapshot, create_recommendations
from backend.src.recommendation_contract import RecommendationRequest
from backend.src.scoring import recommend_financing
from test_financing import CAFE, PRODUCT, AT


class FakeStore:
    def __init__(self):
        self.company = deepcopy(CAFE)
        self.records = {}
        self.missing = False
        self.fail_audit = False

    def load_authorized_snapshot(self, actor, company_id):
        if self.missing:
            return None
        return AuthorizedSnapshot(company_id, "profile-1", "catalog-1", self.company, [PRODUCT])

    def save_audit(self, key, record):
        if self.fail_audit:
            raise RuntimeError("private database failure")
        self.records[key] = deepcopy(record)


class RecommendationApiTests(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router, prefix="/api/v1")
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)
        testing_session = sessionmaker(bind=self.engine)

        def override_get_db():
            with testing_session() as db:
                yield db

        self.app.dependency_overrides[get_db] = override_get_db
        self.store = FakeStore()
        self.app.dependency_overrides[get_recommendation_actor] = lambda: Actor("u1", "c1")
        self.app.dependency_overrides[get_recommendation_store] = lambda: self.store
        self.client = TestClient(self.app)
        self.request = dict(purpose="goods", amount=800000, termMonths=24)

    def tearDown(self):
        self.client.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    def post(self, **changes):
        return self.client.post("/api/v1/recommendations", json=self.request | changes)

    def test_success_and_saved_audit(self):
        response = self.post()
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertEqual(result["companyId"], "c1")
        record = self.store.records[result["evaluationId"]]
        self.assertEqual(record["result"], result)
        self.assertEqual(record["inputs"]["company"], CAFE)
        self.assertEqual(len(record["inputSha256"]), 64)

    def test_missing_auth_cannot_be_supplied_by_headers_or_query(self):
        del self.app.dependency_overrides[get_recommendation_actor]
        response = self.client.post("/api/v1/recommendations?user_id=u1",
                                    json=self.request, headers={"X-User-Id": "u1"})
        self.assertEqual(response.status_code, 401)
        self.assertFalse(self.store.records)

    def test_other_company_and_missing_company_indistinguishable(self):
        other = self.post(companyId="other")
        self.store.missing = True
        missing = self.post()
        self.assertEqual(other.status_code, 404)
        self.assertEqual(other.json(), missing.json())
        self.assertFalse(self.store.records)

    def test_reject_client_financial_overrides_and_invalid_input(self):
        for changes in ({"score": 100}, {"monthlyRevenue": 99999999},
                        {"amount": True}, {"amount": 0}, {"termMonths": True},
                        {"amount": "1.001"}, {"preference": "magic"}):
            with self.subTest(changes=changes):
                self.assertEqual(self.post(**changes).status_code, 422)
        self.assertFalse(self.store.records)

    def test_invalid_source_is_not_a_rejection(self):
        self.store.company["monthlyRevenue"] = None
        response = self.post()
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["detail"]["code"], "SOURCE_DATA_INVALID")
        self.assertFalse(self.store.records)

    def test_audit_failure_never_returns_success_or_database_message(self):
        self.store.fail_audit = True
        response = self.post()
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private", response.text)

    def test_sql_store_missing_actor_and_openapi(self):
        del self.app.dependency_overrides[get_recommendation_store]
        self.assertEqual(self.post().status_code, 404)
        schema = self.app.openapi()
        self.assertIn("RecommendationResponse", schema["components"]["schemas"])
        request = schema["components"]["schemas"]["RecommendationRequest"]
        self.assertFalse(request["additionalProperties"])

    def test_audit_replay(self):
        result = create_recommendations(RecommendationRequest(**self.request), Actor("u1", "c1"),
                                        self.store, evaluated_at=AT)
        record = self.store.records[result.evaluationId]
        inputs = record["inputs"]
        replay = recommend_financing(inputs["company"], inputs["products"], purpose="goods",
                                     amount=inputs["request"]["amount"], term_months=24,
                                     evaluated_at=AT)
        self.assertEqual(replay["groups"]["requested"][0]["evaluation"]["scoring"]["score"],
                         record["result"]["groups"]["requested"][0]["evaluation"]["scoring"]["score"])
