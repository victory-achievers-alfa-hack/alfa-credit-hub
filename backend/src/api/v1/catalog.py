from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.src.dependency import get_db
from backend.src.service import catalog as catalog_service


router = APIRouter()


@router.get("/credit-products")
def get_credit_products(user_id: int, db: Session = Depends(get_db)) -> list[dict]:
    return catalog_service.get_credit_products(user_id, db)