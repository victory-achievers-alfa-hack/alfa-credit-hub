from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from backend.src.dependency import CurrentUser
from backend.src.models import (
    Application,
    ApplicationCheck,
    ApplicationDocument,
    ApplicationEvent,
    Company,
    CompanyDocument,
    CreditProduct,
    OfferDecision,
    User,
)
from backend.src.schemas import applications as application_schemas
from backend.src.schemas.enums import ApplicationStatus
from backend.src.scoring.financing import POLICY_VERSION, loan_quote, assess_financing
from backend.src.scoring.rules import InputError
from backend.src.service.application_state import ensure_application_transition


def get_applications(
    company_id: str | None,
    status: ApplicationStatus | None,
    limit: int,
    offset: int,
    db: Session,
) -> application_schemas.ApplicationListResponse:
    if company_id is None:
        return application_schemas.ApplicationListResponse(
            items=[], total=0, limit=limit, offset=offset
        )

    query = select(Application).where(Application.company_id == company_id)
    if status is not None:
        query = query.where(Application.status == status.value)
    count_query = (
        select(func.count())
        .select_from(Application)
        .where(Application.company_id == company_id)
    )
    if status is not None:
        count_query = count_query.where(Application.status == status.value)
    total = db.scalar(count_query) or 0
    applications = db.scalars(
        query.options(selectinload(Application.product))
        .order_by(Application.updated_at.desc(), Application.id)
        .limit(limit)
        .offset(offset)
    ).all()
    return application_schemas.ApplicationListResponse(
        items=[
            application_schemas.ApplicationListItemResponse(
                id=application.id,
                company_id=application.company_id,
                company_name=application.company.name,
                product_id=application.product_id,
                product_name=application.product.name,
                purpose=application.purpose,
                amount=application.amount,
                term_months=application.term_months,
                status=application.status,
                updated_at=application.updated_at,
            )
            for application in applications
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


def set_application(
    request: application_schemas.ApplicationCreateRequest,
    user: CurrentUser,
    db: Session,
) -> application_schemas.ApplicationDetailResponse:
    company, actor = _get_client_company_and_user(user, db)
    product = db.get(CreditProduct, request.product_id)
    if product is None:
        raise _not_found("Credit product not found")

    now = datetime.now(timezone.utc)
    company_snapshot = _company_snapshot(company)
    product_snapshot = _product_snapshot(product)
    try:
        assessment = assess_financing(
            company_snapshot,
            product_snapshot,
            purpose=request.purpose.value,
            amount=request.amount,
            term_months=request.term_months,
            evaluated_at=now,
        )
    except InputError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "SOURCE_DATA_INVALID",
                "message": "Для оформления заявки нужно уточнить данные компании или продукта.",
            },
        ) from exc

    application_id = _next_application_id(db, now.year)
    application = Application(
        id=application_id,
        company_id=company.id,
        product_id=product.id,
        created_by_user_id=actor.id,
        purpose=request.purpose.value,
        amount=request.amount,
        term_months=request.term_months,
        requested_rate=Decimal(str(assessment["rate"])),
        status=ApplicationStatus.REVIEW.value,
        created_at=now,
        updated_at=now,
    )
    scoring = assessment["scoring"]
    snapshot = ApplicationCheck(
        application_id=application_id,
        rules_version=POLICY_VERSION,
        score=scoring["score"],
        risk=scoring["riskLevel"],
        rate=Decimal(str(assessment["rate"])),
        coverage=Decimal(str(assessment["coverage"])),
        monthly_payment=Decimal(str(assessment["monthlyPayment"])),
        max_available_amount=Decimal(
            str(assessment.get("recommendedAmount") or product.max_amount)
        ),
        eligible=assessment["eligible"],
        explanation=scoring["summary"],
        input_data={
            "company": company_snapshot,
            "product": product_snapshot,
            "purpose": request.purpose.value,
            "amount": str(request.amount),
            "termMonths": request.term_months,
            "assessment": assessment["assessment"],
            "actions": assessment["actions"],
            "requiredCoverage": assessment["requiredCoverage"],
            "scoring": assessment["scoring"],
            "calculatedAt": scoring["calculatedAt"],
        },
        factors=scoring["factors"],
        checks=assessment["checks"],
        created_at=now,
    )
    event = ApplicationEvent(
        id=f"EV-{application_id}-001",
        application_id=application_id,
        old_status=None,
        new_status=ApplicationStatus.REVIEW.value,
        actor_id=actor.id,
        actor_role="client",
        event_type="submitted",
        title="Заявка отправлена",
        description="Данные переданы на рассмотрение в банк.",
        created_at=now,
    )
    db.add_all((application, snapshot, event))
    _commit(db)
    return _application_response(_load_application(db, application_id))


def get_application_by_id(
    application_id: str,
    user: CurrentUser,
    db: Session,
) -> application_schemas.ApplicationDetailResponse:
    return _application_response(_get_owned_application(application_id, user, db))


def provide_application_info(
    application_id: str,
    request: application_schemas.AdditionalInfoRequest,
    user: CurrentUser,
    db: Session,
) -> application_schemas.ApplicationDetailResponse:
    application = _get_owned_application(application_id, user, db)
    actor = _get_client_user(user, db)
    ensure_application_transition(
        application.status, "review", "client", "provide_info"
    )
    document_ids = set(request.document_ids)
    if document_ids:
        documents = db.scalars(
            select(CompanyDocument).where(
                CompanyDocument.id.in_(document_ids),
                CompanyDocument.company_id == application.company_id,
            )
        ).all()
        if len(documents) != len(document_ids):
            raise _not_found("Company document not found")
        existing_ids = {
            link.document_id
            for link in db.scalars(
                select(ApplicationDocument).where(
                    ApplicationDocument.application_id == application.id
                )
            ).all()
        }
        db.add_all(
            ApplicationDocument(
                application_id=application.id,
                document_id=document.id,
                company_id=application.company_id,
                attached_by_user_id=actor.id,
            )
            for document in documents
            if document.id not in existing_ids
        )

    _transition_event(
        application,
        "review",
        actor,
        "additional_info_provided",
        "Дополнительные сведения отправлены",
        request.comment,
    )
    application.bank_comment = request.comment
    _commit(db)
    return _application_response(_load_application(db, application_id))


def accept_application(
    application_id: str,
    request: application_schemas.OfferDecisionRequest,
    user: CurrentUser,
    db: Session,
) -> application_schemas.ApplicationDetailResponse:
    application = _get_owned_application(application_id, user, db)
    actor = _get_client_user(user, db)
    target = "sign" if request.accepted else "rejected"
    action = "accept_offer" if request.accepted else "decline_offer"
    ensure_application_transition(application.status, target, "client", action)
    _transition_event(
        application,
        target,
        actor,
        "offer_accepted" if request.accepted else "offer_declined",
        "Предложение принято" if request.accepted else "Предложение отклонено",
        "Клиент подтвердил предложенные условия."
        if request.accepted
        else "Клиент отказался от предложенных условий.",
    )
    _commit(db)
    return _application_response(_load_application(db, application_id))


def sign_application(
    application_id: str,
    user: CurrentUser,
    db: Session,
) -> application_schemas.ApplicationDetailResponse:
    application = _get_owned_application(application_id, user, db)
    actor = _get_client_user(user, db)
    ensure_application_transition(application.status, "ready", "client", "sign")
    _transition_event(
        application,
        "ready",
        actor,
        "application_signed",
        "Договор подписан",
        "Клиент подписал кредитный договор.",
    )
    _commit(db)
    return _application_response(_load_application(db, application_id))


def disburse_application(
    application_id: str,
    user: CurrentUser,
    db: Session,
) -> application_schemas.ApplicationDetailResponse:
    application = _get_owned_application(application_id, user, db)
    actor = _get_client_user(user, db)
    ensure_application_transition(application.status, "disbursed", "client", "disburse")
    _transition_event(
        application,
        "disbursed",
        actor,
        "credit_disbursed",
        "Кредит выдан",
        "Выдача кредита подтверждена.",
    )
    _commit(db)
    return _application_response(_load_application(db, application_id))


def _get_client_company_and_user(
    user: CurrentUser, db: Session
) -> tuple[Company, User]:
    actor = _get_client_user(user, db)
    if actor.company_id is None:
        raise _not_found("Company not found")
    company = db.scalar(
        select(Company)
        .options(selectinload(Company.documents))
        .where(Company.id == actor.company_id)
    )
    if company is None:
        raise _not_found("Company not found")
    return company, actor


def _get_client_user(user: CurrentUser, db: Session) -> User:
    actor = db.scalar(
        select(User).where(
            User.public_id == user.id,
            User.role == "client",
            User.company_id == user.company_id,
        )
    )
    if actor is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHENTICATED", "message": "Authentication required"},
        )
    return actor


def _get_owned_application(
    application_id: str, user: CurrentUser, db: Session
) -> Application:
    if user.company_id is None:
        raise _not_found("Application not found")
    application = _load_application(db, application_id)
    if application is None or application.company_id != user.company_id:
        raise _not_found("Application not found")
    return application


def _load_application(
    db: Session, application_id: str, *, for_update: bool = False
) -> Application | None:
    query = (
        select(Application)
        .options(
            selectinload(Application.company).selectinload(Company.documents),
            selectinload(Application.product),
            selectinload(Application.creator),
            selectinload(Application.assessments),
            selectinload(Application.events).selectinload(ApplicationEvent.actor),
            selectinload(Application.decisions),
        )
        .where(Application.id == application_id)
    )
    if for_update:
        query = query.with_for_update()
    return db.scalar(query)


def _application_response(
    application: Application | None,
) -> application_schemas.ApplicationDetailResponse:
    if application is None:
        raise _not_found("Application not found")
    assessment = max(
        application.assessments, key=lambda item: item.created_at, default=None
    )
    if assessment is None:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "ASSESSMENT_NOT_FOUND",
                "message": "Снимок скоринга отсутствует.",
            },
        )
    offer_decision = max(
        (
            decision
            for decision in application.decisions
            if decision.kind in ("approve", "alternative")
        ),
        key=lambda item: item.created_at,
        default=None,
    )
    offer = None
    if offer_decision is not None:
        quote = loan_quote(
            offer_decision.amount,
            offer_decision.rate,
            offer_decision.term_months,
        )
        offer = application_schemas.ApplicationOfferResponse(
            id=offer_decision.id,
            amount=offer_decision.amount,
            term_months=offer_decision.term_months,
            rate=offer_decision.rate,
            monthly_payment=Decimal(str(quote["monthlyPayment"])),
            reason=offer_decision.comment or "Предложение банка",
            created_at=offer_decision.created_at,
        )
    scoring = application_schemas.ScoringResultResponse(
        score=assessment.score,
        risk_level=assessment.risk,
        summary=assessment.explanation,
        model_version=assessment.input_data.get("scoring", {}).get("modelVersion"),
        feature_version=assessment.input_data.get("scoring", {}).get("featureVersion"),
        calculated_at=assessment.created_at,
        event_probability=None,
        factors=assessment.factors,
    )
    checks = [
        application_schemas.ApplicationCheckResponse.model_validate(check)
        for check in assessment.checks
    ]
    events = [
        application_schemas.ApplicationEventResponse(
            id=event.id,
            status=event.new_status,
            title=event.title,
            description=event.description,
            actor=(
                application.company.name
                if event.actor_role == "client"
                else event.actor.contact_name
                if event.actor is not None
                else "Система"
            ),
            created_at=event.created_at,
        )
        for event in application.events
    ]
    return application_schemas.ApplicationDetailResponse(
        actions=[action for action in assessment.input_data.get("actions", []) if action["code"] != "SUBMIT_APPLICATION"] if application.status in ("review", "need_info") else [],
        required_coverage=assessment.input_data.get("requiredCoverage", 1.25),
        id=application.id,
        company_id=application.company_id,
        product_id=application.product_id,
        product_name=application.product.name,
        purpose=application.purpose,
        requested_amount=application.amount,
        requested_term_months=application.term_months,
        requested_rate=application.requested_rate,
        requested_monthly_payment=assessment.monthly_payment,
        coverage=assessment.coverage,
        status=application.status,
        scoring=scoring,
        checks=checks,
        offer=offer,
        bank_comment=application.bank_comment,
        info_request=application.bank_comment
        if application.status == ApplicationStatus.NEED_INFO.value
        else None,
        created_at=application.created_at,
        updated_at=application.updated_at,
        events=events,
    )


def _company_snapshot(company: Company) -> dict:
    return {
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
            {"id": document.id, "kind": document.kind, "status": document.status}
            for document in sorted(company.documents, key=lambda item: item.id)
        ],
    }


def _product_snapshot(product: CreditProduct) -> dict:
    return {
        "id": product.id,
        "name": product.name,
        "minAmount": str(product.min_amount),
        "maxAmount": str(product.max_amount),
        "rate": str(product.rate),
        "terms": list(product.terms),
        "purposes": list(product.purposes),
    }


def _next_application_id(db: Session, year: int) -> str:
    prefix = f"APP-{year}-"
    existing_ids = db.scalars(
        select(Application.id).where(Application.id.like(f"{prefix}%"))
    ).all()
    sequence = (
        max(
            (
                int(application_id[len(prefix) :])
                for application_id in existing_ids
                if application_id[len(prefix) :].isdigit()
            ),
            default=0,
        )
        + 1
    )
    return f"{prefix}{sequence:03d}"


def _transition_event(
    application: Application,
    target_status: str,
    actor: User,
    event_type: str,
    title: str,
    description: str,
) -> None:
    old_status = application.status
    application.status = target_status
    application.updated_at = datetime.now(timezone.utc)
    application.events.append(
        ApplicationEvent(
            old_status=old_status,
            new_status=target_status,
            actor_id=actor.id,
            actor_role=actor.role,
            event_type=event_type,
            title=title,
            description=description,
            created_at=application.updated_at,
        )
    )


def _commit(db: Session) -> None:
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def _not_found(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "RESOURCE_NOT_FOUND", "message": message},
    )
