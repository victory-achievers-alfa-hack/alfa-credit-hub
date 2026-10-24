from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.src.auth import (
    ACCESS_TOKEN_TTL_SECONDS,
    create_access_token,
    verify_password,
)
from backend.src.models import User
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
    pass
