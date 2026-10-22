from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.src.dependency import get_db
from backend.src.service import catalog as catalog_service
from backend.src.schemas import catalog as catalog_schemas


router = APIRouter()


@router.get("/credit-products")
def get_credit_products(
        user_id: int,
        db: Session = Depends(get_db)
) -> catalog_schemas.CreditProductResponse:
    return catalog_service.get_credit_products(user_id, db)