from sqlalchemy.orm import Session

from backend.src.schemas import recommendations as recommendations_schemas


def set_recommendations(
        request: recommendations_schemas.RecommendationRequest,
        company_id: str | None,
        db: Session
) -> recommendations_schemas.RecommendationResponse:
    pass
