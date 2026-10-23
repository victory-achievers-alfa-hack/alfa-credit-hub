from datetime import datetime

from pydantic import Field

from .base import ApiSchema


class NotificationResponse(ApiSchema):
    id: str
    type: str
    title: str
    text: str
    is_read: bool
    created_at: datetime


class NotificationListResponse(ApiSchema):
    items: list[NotificationResponse]
    total: int = Field(..., ge=0)


class RealtimeEvent(ApiSchema):
    id: str
    sent_at: datetime
    type: str
    payload: dict
