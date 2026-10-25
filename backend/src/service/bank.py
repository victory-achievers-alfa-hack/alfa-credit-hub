from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from backend.src.dependency import CurrentUser
from backend.src.models import Application, Company, Notification, OfferDecision, User, RecommendationAudit
from backend.src.schemas import applications as application_schemas
from backend.src.schemas import bank as bank_schemas
from backend.src.schemas.enums import ApplicationStatus, BankDecisionKind
from backend.src.service import applications as applications_service
from backend.src.service import profile as profile_service
from backend.src.service.application_state import ensure_application_transition
from backend.src.service.realtime import realtime_connections
from backend.src.scoring import assess_financing, InputError
from backend.src.scoring.stress import stress_summary


def get_bank_applications(
    limit: int,
    offset: int,
    db: Session,
) -> bank_schemas.BankApplicationListResponse:
    total = db.scalar(select(func.count()).select_from(Application)) or 0
    applications = db.scalars(
        select(Application)
        .options(selectinload(Application.company), selectinload(Application.product))
        .order_by(Application.updated_at.desc(), Application.id)
        .limit(limit)
        .offset(offset)
    ).all()
    return bank_schemas.BankApplicationListResponse(
        items=[
            bank_schemas.BankApplicationListItemResponse(
                id=application.id,
                company_id=application.company_id,
                company_name=application.company.name,
                product_name=application.product.name,
                amount=application.amount,
                status=application.status,
            )
            for application in applications
        ],
        total=total,
    )


def get_bank_application_by_id(
    id: str, user: CurrentUser, db: Session
) -> bank_schemas.BankApplicationDetailResponse:
    application = applications_service._load_application(db, id)
    if application is None:
        raise _not_found()
    return bank_schemas.BankApplicationDetailResponse(
        application=applications_service._application_response(application),
        company=profile_service.get_user_companies(application.company_id, db),
    )


async def make_bank_decision(
    application_id: str,
    request: bank_schemas.BankDecisionRequest,
    user: CurrentUser,
    db: Session,
) -> application_schemas.ApplicationDetailResponse:
    actor = db.scalar(
        select(User).where(User.public_id == user.id, User.role == "bank")
    )
    if actor is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHENTICATED", "message": "Authentication required"},
        )

    application = applications_service._load_application(
        db, application_id, for_update=True
    )
    if application is None:
        raise _not_found()

    decision_kind = request.kind.value
    if request.kind in (BankDecisionKind.APPROVE, BankDecisionKind.ALTERNATIVE):
        target_status = ApplicationStatus.OFFER.value
        ensure_application_transition(
            application.status, target_status, "bank", decision_kind
        )
        amount = request.amount if request.amount is not None else application.amount
        term_months = (
            request.term_months
            if request.term_months is not None
            else application.term_months
        )
        rate = request.rate if request.rate is not None else application.requested_rate
        if request.kind == BankDecisionKind.APPROVE and (
            amount != application.amount or term_months != application.term_months
            or rate != application.requested_rate
        ):
            raise HTTPException(409, detail={"code": "USE_ALTERNATIVE", "message": "Изменённые условия оформляются как альтернативное предложение."})
        # Re-evaluate current data; a stored score is not a permanent approval.
        product_snapshot = applications_service._product_snapshot(application.product)
        product_snapshot["rate"] = str(rate)
        try:
            assessment = assess_financing(
                applications_service._company_snapshot(application.company), product_snapshot,
                purpose=application.purpose, amount=amount, term_months=term_months,
                evaluated_at=datetime.now(timezone.utc),
            )
        except InputError as exc:
            raise HTTPException(409, detail={"code": "SOURCE_DATA_INVALID", "message": "Для решения нужно уточнить данные или условия."}) from exc
        if not assessment["policyPasses"]:
            raise HTTPException(409, detail={"code": "OFFER_NOT_ELIGIBLE", "message": "Предложенные условия не проходят текущие проверки. " + " ".join(r["message"] for r in assessment["reasons"])})
        if assessment["reviewRequired"] and len((request.comment or "").strip()) < 20:
            raise HTTPException(409, detail={"code": "REVIEW_JUSTIFICATION_REQUIRED", "message": "Для балла 50–69 укажите обоснование решения: не менее 20 символов."})
        assessment["stress"] = stress_summary(applications_service._company_snapshot(application.company), product_snapshot, purpose=application.purpose, amount=amount, term_months=term_months, evaluated_at=datetime.fromisoformat(assessment["calculatedAt"].replace("Z", "+00:00")))
        comment = request.comment.strip() if request.comment else None
        title = (
            "Заявка одобрена"
            if request.kind == BankDecisionKind.APPROVE
            else "Банк предложил другие условия"
        )
        description = comment or "Банк сформировал кредитное предложение."
        notification_tone = (
            "positive" if request.kind == BankDecisionKind.APPROVE else "warning"
        )
    elif request.kind == BankDecisionKind.NEED_INFO:
        target_status = ApplicationStatus.NEED_INFO.value
        ensure_application_transition(
            application.status, target_status, "bank", "request_info"
        )
        amount = term_months = rate = None
        comment = request.comment
        title = "Банку нужны дополнительные сведения"
        description = comment or "Пожалуйста, предоставьте дополнительные сведения."
        notification_tone = "warning"
    else:
        target_status = ApplicationStatus.REJECTED.value
        ensure_application_transition(
            application.status, target_status, "bank", "reject"
        )
        amount = term_months = rate = None
        comment = request.comment
        title = "По заявке принято решение"
        description = comment or "Банк отклонил заявку."
        notification_tone = "negative"

    now = datetime.now(timezone.utc)
    decision = OfferDecision(
        id=f"DEC-{uuid4().hex}",
        application_id=application.id,
        actor_id=actor.id,
        kind=decision_kind,
        amount=amount,
        term_months=term_months,
        rate=rate,
        comment=comment,
        created_at=now,
    )
    if request.kind in (BankDecisionKind.APPROVE, BankDecisionKind.ALTERNATIVE):
        db.add(RecommendationAudit(
            evaluation_id=decision.id, actor_id=user.id, company_id=application.company_id,
            record={"schemaVersion": "bank-decision-audit-v1", "applicationId": application.id,
                "decisionId": decision.id, "kind": decision_kind, "comment": comment,
                "company": applications_service._company_snapshot(application.company),
                "product": product_snapshot, "result": assessment},
        ))
    application.decisions.append(decision)
    application.bank_comment = comment
    applications_service._transition_event(
        application,
        target_status,
        actor,
        f"bank_{decision_kind}",
        title,
        description,
    )

    client = application.creator
    notification = Notification(
        id=f"NTF-{uuid4().hex}",
        user_id=client.id,
        company_id=application.company_id,
        application_id=application.id,
        type=notification_tone,
        title=title,
        text=description,
        created_at=now,
    )
    db.add(notification)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    response = applications_service._application_response(
        applications_service._load_application(db, application_id)
    )
    application_event = {
        "type": "application.updated",
        "companyId": application.company_id,
        "applicationId": application.id,
        "status": application.status,
        "payload": {"application": response.model_dump(mode="json", by_alias=True)},
    }
    notification_event = {
        "type": "notification.created",
        "userId": client.public_id,
        "payload": {
            "notification": {
                "id": notification.id,
                "companyId": application.company_id,
                "applicationId": application.id,
                "title": notification.title,
                "message": notification.text,
                "tone": notification.type,
                "createdAt": notification.created_at.isoformat(),
                "read": False,
            }
        },
    }
    await realtime_connections.publish(application_event)
    await realtime_connections.publish(notification_event)
    return response


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "RESOURCE_NOT_FOUND", "message": "Application not found"},
    )
