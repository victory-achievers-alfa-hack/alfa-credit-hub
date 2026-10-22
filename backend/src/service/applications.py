from sqlalchemy.orm import Session

from backend.src.schemas import applications as application_schemas


def get_applications(
        company: application_schemas.CompanyRequest,
        db: Session
) -> application_schemas.ApplicationListItemResponse:
    pass


def set_application(
        request: application_schemas.ApplicationCreateRequest,
        db: Session
) -> application_schemas.ApplicationDetailResponse:
    pass


def get_application_by_id(
        id: int,
        db: Session
) -> application_schemas.ApplicationDetailResponse:
    pass


def provide_application_info(
        id: int,
        db: Session
) -> application_schemas.ApplicationHistoryEvent:
    pass


def accept_application(
        id: int,
        db: Session
) -> application_schemas.ApplicationHistoryEvent:
    pass


def sign_application(
        id: int,
        db: Session
) -> application_schemas.ApplicationHistoryEvent:
    pass


def disburse_application(
        id: int,
        db: Session
) -> application_schemas.ApplicationHistoryEvent:
    pass