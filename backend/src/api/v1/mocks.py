from backend.src.dependency import get_db
from backend.src.schemas import mocks as mocks_schemas
from backend.src.service import mocks as mocks_service
from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/mocks/fns/{inn}")
def get_mock_fns_check(
    inn: str = Path(..., pattern=r"^\d{10,12}$"), db: Session = Depends(get_db)
) -> mocks_schemas.FnsMockResponse:
    return mocks_service.get_mock_fns_check(inn, db)


@router.get("/mocks/bki/{inn}")
def get_mock_bki_check(
    inn: str = Path(..., pattern=r"^\d{10,12}$"), db: Session = Depends(get_db)
) -> mocks_schemas.BkiMockResponse:
    return mocks_service.get_mock_bki_check(inn, db)
