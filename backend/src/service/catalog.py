from sqlalchemy.orm import Session

from backend.src.schemas import catalog as catalog_schemas


def get_credit_products(
        db: Session
) -> list[catalog_schemas.CreditProductResponse]:
    pass
