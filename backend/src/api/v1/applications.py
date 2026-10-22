from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.src.dependency import get_db
from backend.src.service import applications as applications_service


router = APIRouter()


@router.get("/applications")
def get_applications(company_id: int, db: Session = Depends(get_db)) -> list[dict]:
    return applications_service.get_applications(company_id, db)


@router.post("/applications")
def set_application(company_id: int, db: Session = Depends(get_db)) -> list[dict]:
    return applications_service.set_application(company_id, db)


@router.get("/applications/{id}")
def get_application_by_id(id: int, db: Session = Depends(get_db)) -> dict:
    return applications_service.get_application_by_id(id, db)


@router.post("/applications/{id}/provide-info")
def provide_application_info(id: int, db: Session = Depends(get_db)) -> dict:
    return applications_service.provide_application_info(id, db)


@router.post("/applications/{id}/accept")
def accept_application(id: int, db: Session = Depends(get_db)) -> dict:
    return applications_service.accept_application(id, db)


@router.post("/applications/{id}/sign")
def sign_application(id: int) -> dict:
    return applications_service.sign_application(id)


@router.post("/applications/{id}/disburse")
def disburse_application(id: int) -> dict:
    return applications_service.disburse_application(id)