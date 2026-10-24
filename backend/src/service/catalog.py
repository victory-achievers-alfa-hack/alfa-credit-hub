from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.src.models import CreditProduct
from backend.src.schemas import catalog as catalog_schemas


def get_credit_products(db: Session) -> list[catalog_schemas.CreditProductResponse]:
    products = db.scalars(select(CreditProduct).order_by(CreditProduct.id)).all()
    return [
        catalog_schemas.CreditProductResponse.model_validate(item) for item in products
    ]
