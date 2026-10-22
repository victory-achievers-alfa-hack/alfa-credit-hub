from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.src.dependency import get_db
from backend.src.service import recommendations as recommendations_service


router = APIRouter()


@router.post("/recommendations")
def set_recommendations(user_id: int, db: Session = Depends(get_db)) -> None:
    recommendations_service.set_recommendations(user_id, db)