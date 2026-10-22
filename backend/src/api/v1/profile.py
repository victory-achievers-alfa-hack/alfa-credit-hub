from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.src.dependency import get_db
from backend.src.service import profile as profile_service


router = APIRouter()


@router.get("/me")
def get_user_data(user_id: int, db: Session = Depends(get_db)) -> dict:
    return profile_service.get_user_data(user_id, db)


@router.get("/companies/me")
def get_user_companies(user_id: int, db: Session = Depends(get_db)) -> list[dict]:
    return profile_service.get_user_companies(user_id, db)
