"""Requires trusted data and durable audit adapters; no demo fallback."""

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Protocol
from uuid import uuid4

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.src.models import Company, CreditProduct, RecommendationAudit, User
from backend.src.recommendation_contract import (
    RecommendationRequest,
    RecommendationResponse,
)
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
    def load_authorized_snapshot(
        self, actor: Actor, company_id: str
    ) -> AuthorizedSnapshot | None:
        """Read ownership and versioned data consistently. None for missing OR forbidden.

        Snapshot must contain JSON-compatible server data, not client financial fields.
        """
        ...

    def save_audit(self, evaluation_id: str, record: dict) -> None:
        """Atomically persist an immutable record before returning."""
        ...


class SQLAlchemyRecommendationStore:
    """SQLAlchemy-backed, company-authorized recommendation data and audit store."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def load_authorized_snapshot(
        self, actor: Actor, company_id: str
    ) -> AuthorizedSnapshot | None:
        user = self.db.scalar(
            select(User).where(
                User.public_id == actor.user_id,
                User.role == "client",
                User.company_id == company_id,
                User.company_id == actor.company_id,
            )
        )
        if user is None:
            return None

        company = self.db.scalar(
            select(Company)
            .options(selectinload(Company.documents))
            .where(Company.id == company_id)
        )
        if company is None:
            return None

        company_data = {
            "id": company.id,
            "name": company.name,
            "legalName": company.legal_name,
            "inn": company.inn,
            "okved": company.okved,
            "registrationDate": company.registration_date.isoformat(),
            "account": company.account,
            "representative": company.representative,
            "monthlyRevenue": str(company.monthly_revenue),
            "monthlyExpenses": str(company.monthly_expenses),
            "existingPayments": str(company.current_monthly_debt_payment),
            "hasOverdue": company.has_overdue,
            "active": company.active,
            "scoringScore": company.scoring_score,
            "documents": [
                {
                    "id": document.id,
                    "kind": document.kind,
                    "status": document.status,
                }
                for document in sorted(company.documents, key=lambda item: item.id)
            ],
        }
        product_data = [
            {
                "id": product.id,
                "name": product.name,
                "minAmount": str(product.min_amount),
                "maxAmount": str(product.max_amount),
                "rate": str(product.rate),
                "terms": list(product.terms),
                "purposes": list(product.purposes),
                "shortName": product.short_name,
                "description": product.description,
                "accent": product.accent,
            }
            for product in self.db.scalars(
                select(CreditProduct).order_by(CreditProduct.id)
            ).all()
        ]
        profile_version = _snapshot_version(company_data)
        catalog_version = _snapshot_version(product_data)
        return AuthorizedSnapshot(
            company_id=company_id,
            profile_version=profile_version,
            catalog_version=catalog_version,
            company=company_data,
            products=product_data,
        )

    def save_audit(self, evaluation_id: str, record: dict) -> None:
        actor_id = record.get("actorId")
        company_id = record.get("companyId")
        if not isinstance(actor_id, str) or not isinstance(company_id, str):
            raise ValueError("Audit record must identify its actor and company")
        user = self.db.scalar(
            select(User).where(
                User.public_id == actor_id,
                User.role == "client",
                User.company_id == company_id,
            )
        )
        if user is None or self.db.get(Company, company_id) is None:
            raise ValueError("Audit actor is not authorized for the company")

        try:
            self.db.add(
                RecommendationAudit(
                    evaluation_id=evaluation_id,
                    actor_id=actor_id,
                    company_id=company_id,
                    record=deepcopy(record),
                )
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise


def _snapshot_version(value: dict | list) -> str:
    canonical = json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


class RecommendationError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status, self.code, self.message = status, code, message
        super().__init__(message)


def create_recommendations(
    request: RecommendationRequest,
    actor: Actor,
    store: RecommendationStore,
    *,
    evaluated_at: datetime | None = None,
) -> RecommendationResponse:
    company_id = request.companyId or actor.company_id
    if company_id != actor.company_id:
        raise RecommendationError(404, "COMPANY_NOT_FOUND", "Компания недоступна.")
    try:
        snapshot = store.load_authorized_snapshot(actor, company_id)
    except Exception as exc:
        raise RecommendationError(
            503, "SOURCE_UNAVAILABLE", "Источник данных временно недоступен."
        ) from exc
    if snapshot is None:
        raise RecommendationError(404, "COMPANY_NOT_FOUND", "Компания недоступна.")
    if (
        not isinstance(snapshot, AuthorizedSnapshot)
        or snapshot.company_id != company_id
        or not snapshot.profile_version
        or not snapshot.catalog_version
        or not isinstance(snapshot.company, dict)
        or not isinstance(snapshot.products, list)
    ):
        raise RecommendationError(
            503, "INVALID_SOURCE", "Не удалось подтвердить версию исходных данных."
        )
    instant = evaluated_at if evaluated_at is not None else datetime.now(timezone.utc)
    company, products = deepcopy(snapshot.company), deepcopy(snapshot.products)
    evaluation_id = str(uuid4())
    try:
        calculation = recommend_financing(
            company,
            products,
            purpose=request.purpose,
            amount=request.amount,
            term_months=request.termMonths,
            preference=request.preference,
            evaluated_at=instant,
        )
        response = RecommendationResponse.model_validate(
            {**calculation, "evaluationId": evaluation_id, "companyId": company_id}
        )
    except InputError as exc:
        raise RecommendationError(
            409, "SOURCE_DATA_INVALID", "Для расчёта нужно уточнить серверные данные."
        ) from exc
    except ValidationError as exc:
        raise RecommendationError(
            503, "CALCULATION_INVALID", "Расчёт временно недоступен."
        ) from exc
    try:
        inputs = {
            "company": company,
            "products": products,
            "request": request.model_dump(mode="json"),
        }
        canonical = json.dumps(
            inputs,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
        record = {
            "schemaVersion": "recommendation-audit-v1",
            "actorId": actor.user_id,
            "versions": {
                "model": MODEL_VERSION,
                "features": FEATURE_VERSION,
                "policy": POLICY_VERSION,
                "ranking": RANKING_VERSION,
            },
            "companyId": company_id,
            "profileVersion": snapshot.profile_version,
            "catalogVersion": snapshot.catalog_version,
            "inputSha256": sha256(canonical.encode()).hexdigest(),
            "inputs": inputs,
            "result": response.model_dump(mode="json"),
        }
        store.save_audit(evaluation_id, record)
    except Exception as exc:
        raise RecommendationError(
            503, "AUDIT_UNAVAILABLE", "Не удалось сохранить результат расчёта."
        ) from exc
    return response
