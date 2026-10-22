from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.src.dependency import get_db
from backend.src.service import bank as bank_service
from backend.src.schemas import bank as bank_schemas


router = APIRouter()


@router.get("/bank/applications")
def get_bank_applications(db: Session = Depends(get_db)) -> list[bank_schemas.BankCheckItem]:
    return bank_service.get_bank_applications(db)


@router.get("/bank/applications/{id}")
def get_bank_application_by_id(
        id: int,
        db: Session = Depends(get_db)
) -> bank_schemas.BankApplicationDetailResponse:
    return bank_service.get_bank_application_by_id(id, db)


@router.post("/bank/applications/{id}/decision")
def make_bank_decision(
        id: int,
        db: Session = Depends(get_db)
) -> bank_schemas.BankDecisionRequest:
    return bank_service.make_bank_decision(id, db)