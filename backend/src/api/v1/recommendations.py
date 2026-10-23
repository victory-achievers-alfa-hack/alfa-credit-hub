from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.src.dependency import CurrentUser, get_db, require_role
from backend.src.service import recommendations as recommendations_service
from backend.src.schemas import recommendations as recommendations_schemas


router = APIRouter()


@router.post("/recommendations")
def set_recommendations(
        request: recommendations_schemas.RecommendationRequest,
        user: CurrentUser = Depends(require_role("client")),
        db: Session = Depends(get_db)
) -> recommendations_schemas.RecommendationResponse:
    return recommendations_service.set_recommendations(request, user.company_id, db)
