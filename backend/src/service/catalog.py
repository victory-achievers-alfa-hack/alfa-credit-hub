from sqlalchemy.orm import Session

from backend.src.schemas import catalog as catalog_schemas


def get_credit_products(
        user_id: int,
        db: Session
) -> catalog_schemas.CreditProductResponse:
    pass