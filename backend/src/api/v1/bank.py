from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.src.dependency import CurrentUser, get_db, require_role
from backend.src.service import bank as bank_service
from backend.src.schemas import bank as bank_schemas
from backend.src.schemas import applications as application_schemas


router = APIRouter()


@router.get("/bank/applications")
def get_bank_applications(
    limit: int = Query(default=20, gt=0, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require_role("bank")),
    db: Session = Depends(get_db),
) -> bank_schemas.BankApplicationListResponse:
    return bank_service.get_bank_applications(limit, offset, db)


@router.get("/bank/applications/{id}")
def get_bank_application_by_id(
    id: str,
    user: CurrentUser = Depends(require_role("bank")),
    db: Session = Depends(get_db),
) -> bank_schemas.BankApplicationDetailResponse:
    return bank_service.get_bank_application_by_id(id, user, db)


@router.post("/bank/applications/{id}/decision")
async def make_bank_decision(
    id: str,
    request: bank_schemas.BankDecisionRequest,
    user: CurrentUser = Depends(require_role("bank")),
    db: Session = Depends(get_db),
) -> application_schemas.ApplicationDetailResponse:
    return await bank_service.make_bank_decision(id, request, user, db)
