from backend.src.auth import authenticate
from backend.src.database import SessionLocal
from backend.src.models import Notification, User, utc_now
from backend.src.schemas import notifications as notification_schemas
from backend.src.service.realtime import realtime_connections
from fastapi import HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session


async def realtime(websocket: WebSocket) -> None:
    authorization = websocket.headers.get("authorization", "")
    token = (
        authorization[7:].strip()
        if authorization.lower().startswith("bearer ")
        else websocket.cookies.get("access_token")
    )
    with SessionLocal() as db:
        user = authenticate(token, db)
    if user is None:
        await websocket.close(code=4401, reason="Authentication required")
        return

    websocket.state.user = user
    await realtime_connections.connect(websocket, user)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        realtime_connections.disconnect(websocket)


def get_notifications(
    user_id: str,
    unread_only: bool,
    limit: int,
    offset: int,
    db: Session,
) -> notification_schemas.NotificationListResponse:
    user = db.scalar(select(User).where(User.public_id == user_id))
    if user is None:
        raise _not_found()

    query = select(Notification).where(Notification.user_id == user.id)
    count_query = (
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == user.id)
    )
    if unread_only:
        query = query.where(Notification.read_at.is_(None))
        count_query = count_query.where(Notification.read_at.is_(None))

    notifications = db.scalars(
        query.order_by(Notification.created_at.desc(), Notification.id)
        .limit(limit)
        .offset(offset)
    ).all()
    return notification_schemas.NotificationListResponse(
        items=[_notification_response(item) for item in notifications],
        total=db.scalar(count_query) or 0,
    )


async def mark_notification_read(
    notification_id: str,
    user_id: str,
    db: Session,
) -> notification_schemas.NotificationResponse:
    user = db.scalar(select(User).where(User.public_id == user_id))
    if user is None:
        raise _not_found()
    notification = db.scalar(
        select(Notification).where(
            Notification.id == notification_id, Notification.user_id == user.id
        )
    )
    if notification is None:
        raise _not_found()

    if notification.read_at is None:
        notification.read_at = utc_now()
        db.commit()
        await realtime_connections.publish(
            {
                "type": "notification.read",
                "userId": user.public_id,
                "payload": {"notificationId": notification.id},
            }
        )
    return _notification_response(notification)


def _notification_response(
    notification: Notification,
) -> notification_schemas.NotificationResponse:
    return notification_schemas.NotificationResponse(
        id=notification.id,
        type=notification.type,
        title=notification.title,
        text=notification.text,
        is_read=notification.read_at is not None,
        created_at=notification.created_at,
    )


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "RESOURCE_NOT_FOUND", "message": "Notification not found"},
    )
