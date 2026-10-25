from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from backend.src.dependency import CurrentUser, get_current_user, get_db, require_role
from backend.src.service import applications as applications_service
from backend.src.schemas import applications as application_schemas
from backend.src.schemas.enums import ApplicationStatus
from backend.src.service.realtime import publish_application_updated


router = APIRouter()


@router.get("/applications")
def get_applications(
    status: ApplicationStatus | None = None,
    limit: int = Query(default=20, gt=0, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require_role("client")),
    db: Session = Depends(get_db),
) -> application_schemas.ApplicationListResponse:
    return applications_service.get_applications(
        user.company_id, status, limit, offset, db
    )


@router.post("/applications")
def set_application(
    request: application_schemas.ApplicationCreateRequest,
    background_tasks: BackgroundTasks,
    user: CurrentUser = Depends(require_role("client")),
    db: Session = Depends(get_db),
) -> application_schemas.ApplicationDetailResponse:
    response = applications_service.set_application(request, user, db)
    background_tasks.add_task(publish_application_updated, response)
    return response


@router.get("/applications/{id}")
def get_application_by_id(
    id: str,
    user: CurrentUser = Depends(require_role("client")),
    db: Session = Depends(get_db),
) -> application_schemas.ApplicationDetailResponse:
    return applications_service.get_application_by_id(id, user, db)


@router.post("/applications/{id}/additional-info")
def provide_application_info(
    id: str,
    request: application_schemas.AdditionalInfoRequest,
    background_tasks: BackgroundTasks,
    user: CurrentUser = Depends(require_role("client")),
    db: Session = Depends(get_db),
) -> application_schemas.ApplicationDetailResponse:
    response = applications_service.provide_application_info(id, request, user, db)
    background_tasks.add_task(publish_application_updated, response)
    return response


@router.post("/applications/{id}/accept")
def accept_application(
    id: str,
    request: application_schemas.OfferDecisionRequest,
    background_tasks: BackgroundTasks,
    user: CurrentUser = Depends(require_role("client")),
    db: Session = Depends(get_db),
) -> application_schemas.ApplicationDetailResponse:
    response = applications_service.accept_application(id, request, user, db)
    background_tasks.add_task(publish_application_updated, response)
    return response


@router.post("/applications/{id}/sign")
def sign_application(
    id: str,
    background_tasks: BackgroundTasks,
    user: CurrentUser = Depends(require_role("client")),
    db: Session = Depends(get_db),
) -> application_schemas.ApplicationDetailResponse:
    response = applications_service.sign_application(id, user, db)
    background_tasks.add_task(publish_application_updated, response)
    return response


@router.post("/applications/{id}/disburse")
def disburse_application(
    id: str,
    background_tasks: BackgroundTasks,
    user: CurrentUser = Depends(require_role("client")),
    db: Session = Depends(get_db),
) -> application_schemas.ApplicationDetailResponse:
    response = applications_service.disburse_application(id, user, db)
    background_tasks.add_task(publish_application_updated, response)
    return response
