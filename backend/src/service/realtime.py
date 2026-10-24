from datetime import datetime, timezone
from uuid import uuid4

from fastapi import WebSocket

from backend.src.dependency import CurrentUser


class RealtimeConnections:
    def __init__(self) -> None:
        self._connections: dict[WebSocket, CurrentUser] = {}

    async def connect(self, websocket: WebSocket, user: CurrentUser) -> None:
        await websocket.accept()
        self._connections[websocket] = user

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.pop(websocket, None)

    async def publish(self, event: dict) -> None:
        """Publish only to principals matching the event's routing metadata."""
        event_type = event.get("type")
        company_id = event.get("companyId")
        user_id = event.get("userId")
        message = {
            "id": str(uuid4()),
            "sentAt": datetime.now(timezone.utc).isoformat(),
            **{
                key: value
                for key, value in event.items()
                if key not in {"companyId", "userId"}
            },
        }
        stale: list[WebSocket] = []

        for websocket, user in self._connections.items():
            if (
                event_type == "notification.created"
                or event_type == "notification.read"
            ):
                allowed = user.id == user_id
            elif user.role == "bank":
                allowed = event_type == "application.updated"
            else:
                allowed = user.role == "client" and user.company_id == company_id
            if not allowed:
                continue
            try:
                await websocket.send_json(message)
            except Exception:
                stale.append(websocket)

        for websocket in stale:
            self.disconnect(websocket)


realtime_connections = RealtimeConnections()
