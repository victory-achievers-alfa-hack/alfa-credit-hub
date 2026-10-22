from sqlalchemy.orm import Session

from backend.src.schemas import system as system_schemas


def reset_demo_db(db: Session) -> system_schemas.StatusMessageResponse:
    pass


def check_health(db: Session) -> system_schemas.HealthCheckResponse:
    pass