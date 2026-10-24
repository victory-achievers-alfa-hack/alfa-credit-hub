from datetime import datetime

from pydantic import Field

from .base import ApiSchema


class NotificationResponse(ApiSchema):
    id: str
    company_id: str | None
    application_id: str | None
    title: str
    message: str
    tone: str
    created_at: datetime
    read: bool


class NotificationListResponse(ApiSchema):
    items: list[NotificationResponse]
    total: int = Field(..., ge=0)


class RealtimeEvent(ApiSchema):
    id: str
    sent_at: datetime
    type: str
    payload: dict
