from sqlalchemy.orm import Session

from backend.src.dependency import CurrentUser
from backend.src.schemas import applications as application_schemas
from backend.src.schemas.enums import ApplicationStatus


def get_applications(
    company_id: str | None,
    status: ApplicationStatus | None,
    limit: int,
    offset: int,
    db: Session,
) -> application_schemas.ApplicationListResponse:
    pass


def set_application(
    request: application_schemas.ApplicationCreateRequest,
    user: CurrentUser,
    db: Session,
) -> application_schemas.ApplicationDetailResponse:
    pass


def get_application_by_id(
    application_id: str,
    user: CurrentUser,
    db: Session,
) -> application_schemas.ApplicationDetailResponse:
    pass


def provide_application_info(
    application_id: str,
    request: application_schemas.AdditionalInfoRequest,
    user: CurrentUser,
    db: Session,
) -> application_schemas.ApplicationDetailResponse:
    pass


def accept_application(
    application_id: str,
    request: application_schemas.OfferDecisionRequest,
    user: CurrentUser,
    db: Session,
) -> application_schemas.ApplicationDetailResponse:
    pass


def sign_application(
    application_id: str,
    user: CurrentUser,
    db: Session,
) -> application_schemas.ApplicationDetailResponse:
    pass


def disburse_application(
    application_id: str,
    user: CurrentUser,
    db: Session,
) -> application_schemas.ApplicationDetailResponse:
    pass
