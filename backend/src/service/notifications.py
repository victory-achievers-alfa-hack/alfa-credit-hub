from sqlalchemy.orm import Session

from backend.src.schemas import notifications as notification_schemas


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
