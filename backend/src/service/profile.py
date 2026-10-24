from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from backend.src.auth import (
    ACCESS_TOKEN_TTL_SECONDS,
    create_access_token,
    verify_password,
)
from backend.src.models import Company, User
from backend.src.scoring import score_company, InputError
from backend.src.schemas import profile as profile_schemas


def login_user(
    login_request: profile_schemas.LoginRequest,
    db: Session,
) -> profile_schemas.LoginResponse:
    email = str(login_request.email).lower()
    user = db.query(User).filter(func.lower(User.email) == email).one_or_none()
    if user is None or not verify_password(login_request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_CREDENTIALS",
                "message": "Invalid email or password",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    return profile_schemas.LoginResponse(
        access_token=create_access_token(user),
        token_type="bearer",
        user=_user_response(user),
    )


def get_user_data(user_id: str, db: Session) -> profile_schemas.UserMeResponse:
    user = db.query(User).filter(User.public_id == user_id).one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHENTICATED", "message": "Authentication required"},
        )
    return _user_response(user)


def _user_response(user: User) -> profile_schemas.UserMeResponse:
    return profile_schemas.UserMeResponse(
        id=user.public_id,
        name=user.contact_name,
        email=user.email,
        role=user.role,
        company_id=user.company_id,
    )


def get_user_companies(
    company_id: str | None, db: Session
) -> profile_schemas.CompanyProfileResponse:
    if company_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "COMPANY_NOT_FOUND", "message": "Company not found"},
        )

    company = db.scalar(
        select(Company)
        .options(selectinload(Company.documents))
        .where(Company.id == company_id)
    )
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "COMPANY_NOT_FOUND", "message": "Company not found"},
        )

    try:
        scoring = score_company({
            "monthlyRevenue": company.monthly_revenue,
            "monthlyExpenses": company.monthly_expenses,
            "existingPayments": company.current_monthly_debt_payment,
            "hasOverdue": company.has_overdue,
            "registrationDate": company.registration_date.isoformat(),
        }, evaluated_at=datetime.now(timezone.utc))
    except InputError as exc:
        raise HTTPException(409, detail={"code": "SOURCE_DATA_INVALID", "message": "Уточните финансовые данные компании."}) from exc

    return profile_schemas.CompanyProfileResponse(
        id=company.id,
        name=company.name,
        legal_name=company.legal_name,
        inn=company.inn,
        okved=company.okved,
        registration_date=company.registration_date,
        account=company.account,
        representative=company.representative,
        monthly_revenue=company.monthly_revenue,
        monthly_expenses=company.monthly_expenses,
        existing_payments=company.current_monthly_debt_payment,
        has_overdue=company.has_overdue,
        active=company.active,
        scoring_score=scoring["score"],
        documents=[
            profile_schemas.CompanyDocumentSchema.model_validate(document)
            for document in sorted(company.documents, key=lambda item: item.id)
        ],
    )
