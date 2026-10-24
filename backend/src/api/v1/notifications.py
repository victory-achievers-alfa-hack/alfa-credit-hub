from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from backend.src.dependency import CurrentUser, get_db, require_role
from backend.src.schemas import notifications as notification_schemas
from backend.src.service import notifications as notifications_service


router = APIRouter()


@router.websocket("/realtime")
async def realtime(websocket: WebSocket) -> None:
    await notifications_service.realtime(websocket)


@router.get("/notifications")
def get_notifications(
    unread_only: bool = Query(default=False, alias="unreadOnly"),
    limit: int = Query(default=20, gt=0, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require_role("client")),
    db: Session = Depends(get_db),
) -> notification_schemas.NotificationListResponse:
    return notifications_service.get_notifications(
        user.id, unread_only, limit, offset, db
    )


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: str,
    user: CurrentUser = Depends(require_role("client")),
    db: Session = Depends(get_db),
) -> notification_schemas.NotificationResponse:
    return notifications_service.mark_notification_read(notification_id, user.id, db)
