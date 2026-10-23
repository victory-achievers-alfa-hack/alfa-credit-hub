from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.src.dependency import CurrentUser, get_current_user, get_db, require_role
from backend.src.service import profile as profile_service
from backend.src.schemas import profile as profile_schemas


router = APIRouter()


@router.post("/auth/login", response_model_exclude_none=True)
def login_user(login_request: profile_schemas.LoginRequest) -> profile_schemas.LoginResponse:
    return profile_service.login_user(login_request)


@router.get("/me")
def get_user_data(
        user: CurrentUser = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> profile_schemas.UserMeResponse:
    return profile_service.get_user_data(user.id, db)


@router.get("/companies/me")
def get_user_companies(
        user: CurrentUser = Depends(require_role("client")),
        db: Session = Depends(get_db)
) -> profile_schemas.CompanyProfileResponse:
    return profile_service.get_user_companies(user.company_id, db)
