from fastapi import APIRouter, Depends, HTTPException
from backend.src.recommendation_contract import RecommendationRequest, RecommendationResponse, ErrorResponse
from backend.src.service.recommendations import Actor, RecommendationStore, RecommendationError, create_recommendations


router = APIRouter()


def get_recommendation_actor() -> Actor:
    # Must be wired to verified session/token auth, never unverified identity headers.
    raise HTTPException(401, detail={"code": "AUTH_REQUIRED", "message": "Требуется авторизация."})


def get_recommendation_store() -> RecommendationStore:
    raise HTTPException(503, detail={"code": "STORE_NOT_CONFIGURED", "message": "Сервис расчёта не подключён."})


@router.post("/recommendations", response_model=RecommendationResponse,
             responses={status: {"model": ErrorResponse} for status in (401, 404, 409, 503)})
def recommendations(request: RecommendationRequest,
                    actor: Actor = Depends(get_recommendation_actor),
                    store: RecommendationStore = Depends(get_recommendation_store)) -> RecommendationResponse:
    try:
        return create_recommendations(request, actor, store)
    except RecommendationError as exc:
        raise HTTPException(exc.status, detail={"code": exc.code, "message": exc.message}) from exc
