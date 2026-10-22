from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.src.dependency import get_db
from backend.src.service import mocks as mocks_service


router = APIRouter()


@router.get("/mocks/fns/{inn}")
def get_mock_fns_check(inn: int, db: Session = Depends(get_db)) -> dict:
    return mocks_service.get_mock_fns_check(inn, db)


@router.get("/mocks/bki/{inn}")
def get_mock_bki_check(inn: int, db: Session = Depends(get_db)) -> dict:
    return mocks_service.get_mock_bki_check(inn, db)