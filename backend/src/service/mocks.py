from backend.src.models import Company
from backend.src.schemas import mocks as mocks_schemas
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session


def get_mock_fns_check(inn: str, db: Session) -> mocks_schemas.FnsMockResponse:
    company = _get_company(inn, db)
    return mocks_schemas.FnsMockResponse(
        inn=company.inn,
        legal_name=company.legal_name,
        is_active=company.active,
        registered_since=company.registration_date,
        okved=company.okved,
    )


def get_mock_bki_check(inn: str, db: Session) -> mocks_schemas.BkiMockResponse:
    company = _get_company(inn, db)
    return mocks_schemas.BkiMockResponse(
        inn=company.inn,
        has_delinquencies=company.has_overdue,
        monthly_debt_load=company.current_monthly_debt_payment,
    )


def _get_company(inn: str, db: Session) -> Company:
    company = db.scalar(select(Company).where(Company.inn == inn))
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "RESOURCE_NOT_FOUND", "message": "Company not found"},
        )
    return company
