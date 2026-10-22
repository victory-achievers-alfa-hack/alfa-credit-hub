from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.src.dependency import get_db
from backend.src.service import profile as profile_service
from backend.src.schemas import profile as profile_schemas


router = APIRouter()


@router.post("/auth/login")
def login_user(login_request: profile_schemas.LoginRequest) -> profile_schemas.LoginResponse:
    return profile_service.login_user(login_request)


@router.get("/me")
def get_user_data(
        user_id: int,
        db: Session = Depends(get_db)
) -> profile_schemas.UserMeResponse:
    return profile_service.get_user_data(user_id, db)


@router.get("/companies/me")
def get_user_companies(
        user_id: int,
        db: Session = Depends(get_db)
) -> profile_schemas.CompanyProfileResponse:
    return profile_service.get_user_companies(user_id, db)
