from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.src.dependency import CurrentUser, get_db, require_role
from backend.src.recommendation_contract import (
    RecommendationRequest,
    RecommendationResponse,
    ErrorResponse,
)
from backend.src.service.recommendations import (
    Actor,
    RecommendationError,
    RecommendationStore,
    SQLAlchemyRecommendationStore,
    create_recommendations,
)


router = APIRouter()


def get_recommendation_actor(
    user: CurrentUser = Depends(require_role("client")),
) -> Actor:
    if user.company_id is None:
        raise HTTPException(
            403,
            detail={
                "code": "FORBIDDEN",
                "message": "У пользователя не указана компания.",
            },
        )
    return Actor(user_id=user.id, company_id=user.company_id)


def get_recommendation_store(
    db: Session = Depends(get_db),
) -> RecommendationStore:
    return SQLAlchemyRecommendationStore(db)


@router.post(
    "/recommendations",
    response_model=RecommendationResponse,
    responses={status: {"model": ErrorResponse} for status in (401, 404, 409, 503)},
)
def recommendations(
    request: RecommendationRequest,
    actor: Actor = Depends(get_recommendation_actor),
    store: RecommendationStore = Depends(get_recommendation_store),
) -> RecommendationResponse:
    try:
        return create_recommendations(request, actor, store)
    except RecommendationError as exc:
        raise HTTPException(
            exc.status, detail={"code": exc.code, "message": exc.message}
        ) from exc
