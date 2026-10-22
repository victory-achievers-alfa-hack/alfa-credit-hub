from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.src.dependency import get_db
from backend.src.service import system as system_service


router = APIRouter()


@router.post("/demo/reset")
def reset_demo_db(db: Session = Depends(get_db)) -> dict:
    return system_service.reset_demo_db(db)


@router.get("/health")
def check_health(db: Session = Depends(get_db)) -> dict:
    return system_service.check_health(db)