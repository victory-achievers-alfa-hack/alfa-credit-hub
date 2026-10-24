from fastapi import WebSocket, WebSocketDisconnect

from sqlalchemy.orm import Session

from backend.src.auth import authenticate
from backend.src.database import SessionLocal
from backend.src.service.realtime import realtime_connections
from backend.src.schemas import notifications as notification_schemas


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
    pass


def mark_notification_read(
    notification_id: str,
    user_id: str,
    db: Session,
) -> notification_schemas.NotificationResponse:
    pass
