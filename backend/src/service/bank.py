from sqlalchemy.orm import Session

from backend.src.dependency import CurrentUser
from backend.src.schemas import bank as bank_schemas
from backend.src.schemas import applications as application_schemas


def get_bank_applications(
        limit: int,
        offset: int,
        db: Session,
) -> bank_schemas.BankApplicationListResponse:
    pass


def get_bank_application_by_id(
        application_id: str,
        db: Session,
) -> bank_schemas.BankApplicationDetailResponse:
    pass


def make_bank_decision(
        application_id: str,
        request: bank_schemas.BankDecisionRequest,
        user: CurrentUser,
        db: Session,
) -> application_schemas.ApplicationDetailResponse:
    pass
