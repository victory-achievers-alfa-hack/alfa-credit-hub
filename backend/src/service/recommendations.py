"""Requires trusted data and durable audit adapters; no demo fallback."""
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Protocol
from uuid import uuid4

from pydantic import ValidationError
from backend.src.recommendation_contract import RecommendationRequest, RecommendationResponse
from backend.src.scoring import InputError, recommend_financing
from backend.src.scoring.rules import MODEL_VERSION, FEATURE_VERSION
from backend.src.scoring.financing import POLICY_VERSION
from backend.src.scoring.ranking import RANKING_VERSION


@dataclass(frozen=True)
class Actor:
    user_id: str
    company_id: str


@dataclass(frozen=True)
class AuthorizedSnapshot:
    company_id: str
    profile_version: str
    catalog_version: str
    company: dict
    products: list[dict]


class RecommendationStore(Protocol):
    def load_authorized_snapshot(self, actor: Actor, company_id: str) -> AuthorizedSnapshot | None:
        """Read ownership and versioned data consistently. None for missing OR forbidden.

        Snapshot must contain JSON-compatible server data, not client financial fields.
        """
        ...

    def save_audit(self, evaluation_id: str, record: dict) -> None:
        """Atomically persist immutable record; commit before returning, raise on failure.

        Enforce unique evaluation_id and access control. Never a production no-op.
        """
        ...


class RecommendationError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status, self.code, self.message = status, code, message
        super().__init__(message)


def create_recommendations(request: RecommendationRequest, actor: Actor,
                           store: RecommendationStore, *, evaluated_at: datetime | None = None
                           ) -> RecommendationResponse:
    company_id = request.companyId or actor.company_id
    if company_id != actor.company_id:
        raise RecommendationError(404, "COMPANY_NOT_FOUND", "Компания недоступна.")
    try:
        snapshot = store.load_authorized_snapshot(actor, company_id)
    except Exception as exc:
        raise RecommendationError(503, "SOURCE_UNAVAILABLE", "Источник данных временно недоступен.") from exc
    if snapshot is None:
        raise RecommendationError(404, "COMPANY_NOT_FOUND", "Компания недоступна.")
    if (not isinstance(snapshot, AuthorizedSnapshot) or snapshot.company_id != company_id
            or not snapshot.profile_version or not snapshot.catalog_version
            or not isinstance(snapshot.company, dict) or not isinstance(snapshot.products, list)):
        raise RecommendationError(503, "INVALID_SOURCE", "Не удалось подтвердить версию исходных данных.")
    instant = evaluated_at if evaluated_at is not None else datetime.now(timezone.utc)
    company, products = deepcopy(snapshot.company), deepcopy(snapshot.products)
    evaluation_id = str(uuid4())
    try:
        calculation = recommend_financing(company, products, purpose=request.purpose,
                                           amount=request.amount, term_months=request.termMonths,
                                           preference=request.preference, evaluated_at=instant)
        response = RecommendationResponse.model_validate({**calculation, "evaluationId": evaluation_id,
                                                           "companyId": company_id})
    except InputError as exc:
        raise RecommendationError(409, "SOURCE_DATA_INVALID", "Для расчёта нужно уточнить серверные данные.") from exc
    except ValidationError as exc:
        raise RecommendationError(503, "CALCULATION_INVALID", "Расчёт временно недоступен.") from exc
    try:
        inputs = {"company": company, "products": products, "request": request.model_dump(mode="json")}
        canonical = json.dumps(inputs, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        record = {"schemaVersion": "recommendation-audit-v1", "actorId": actor.user_id,
                  "versions": {"model": MODEL_VERSION, "features": FEATURE_VERSION,
                               "policy": POLICY_VERSION, "ranking": RANKING_VERSION},
                  "companyId": company_id, "profileVersion": snapshot.profile_version,
                  "catalogVersion": snapshot.catalog_version, "inputSha256": sha256(canonical.encode()).hexdigest(),
                  "inputs": inputs, "result": response.model_dump(mode="json")}
        store.save_audit(evaluation_id, record)
    except Exception as exc:
        raise RecommendationError(503, "AUDIT_UNAVAILABLE", "Не удалось сохранить результат расчёта.") from exc
    return response
