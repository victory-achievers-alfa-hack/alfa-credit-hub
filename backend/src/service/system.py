from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.src.models import (
    Application,
    ApplicationCheck,
    ApplicationDocument,
    ApplicationEvent,
    Company,
    CompanyDocument,
    CreditProduct,
    Notification,
    OfferDecision,
    ScoringRule,
    User,
)
from backend.src.schemas import system as system_schemas
from backend.src.seed import seed_demo_data


def reset_demo_db(db: Session) -> system_schemas.StatusMessageResponse:
    try:
        # Delete dependents before their referenced rows for databases without
        # cascading foreign keys enabled.
        db.query(ApplicationDocument).delete(synchronize_session=False)
        db.query(ApplicationEvent).delete(synchronize_session=False)
        db.query(OfferDecision).delete(synchronize_session=False)
        db.query(ApplicationCheck).delete(synchronize_session=False)
        db.query(Notification).delete(synchronize_session=False)
        db.query(Application).delete(synchronize_session=False)
        db.query(CompanyDocument).delete(synchronize_session=False)
        db.query(User).delete(synchronize_session=False)
        db.query(CreditProduct).delete(synchronize_session=False)
        db.query(Company).delete(synchronize_session=False)
        db.query(ScoringRule).delete(synchronize_session=False)
        db.flush()
        seed_demo_data(db)
    except Exception:
        db.rollback()
        raise
    return system_schemas.StatusMessageResponse(
        message="Демо-данные успешно сброшены к начальному состоянию"
    )


def check_health(db: Session) -> system_schemas.HealthCheckResponse:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "DATABASE_UNAVAILABLE",
                "message": "Database connection is unavailable",
            },
        ) from exc
    return system_schemas.HealthCheckResponse(
        description="Database connection is healthy"
    )
