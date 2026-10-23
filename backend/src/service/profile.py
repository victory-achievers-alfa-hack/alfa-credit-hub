from sqlalchemy.orm import Session

from backend.src.schemas import profile as profile_schemas


def login_user(login_request: profile_schemas.LoginRequest) -> profile_schemas.LoginResponse:
    pass


def get_user_data(
        user_id: str,
        db: Session
) -> profile_schemas.UserMeResponse:
    pass


def get_user_companies(
        company_id: str | None,
        db: Session
) -> profile_schemas.CompanyProfileResponse:
    pass
