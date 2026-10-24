from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.src.dependency import get_db
from backend.src.service import system as system_service
from backend.src.schemas import system as system_schemas


router = APIRouter()


@router.post("/demo/reset")
def reset_demo_db(
    db: Session = Depends(get_db),
) -> system_schemas.StatusMessageResponse:
    return system_service.reset_demo_db(db)


@router.get("/health")
def check_health(db: Session = Depends(get_db)) -> system_schemas.HealthCheckResponse:
    return system_service.check_health(db)
