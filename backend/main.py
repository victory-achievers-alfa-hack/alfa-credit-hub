import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.src.api.v1.applications import router as applications_router
from backend.src.api.v1.assistant import router as assistant_router
from backend.src.api.v1.bank import router as bank_router
from backend.src.api.v1.catalog import router as catalog_router
from backend.src.api.v1.mocks import router as mocks_router
from backend.src.api.v1.notifications import router as notifications_router
from backend.src.api.v1.profile import router as profile_router
from backend.src.api.v1.recommendations import router as recommendations_router
from backend.src.api.v1.system import router as system_router
from backend.src.database import Base, engine
from backend.src.schemas.errors import ErrorResponse

app = FastAPI(responses={
    401: {"model": ErrorResponse, "description": "Authentication required"},
    403: {"model": ErrorResponse, "description": "Role is not allowed"},
    404: {"model": ErrorResponse, "description": "Resource not found"},
    409: {"model": ErrorResponse, "description": "State conflict"},
    422: {"model": ErrorResponse, "description": "Request validation failed"},
    500: {"model": ErrorResponse, "description": "Internal server error"},
})
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        body = detail
    else:
        body = {"code": "HTTP_ERROR", "message": str(detail), "fieldErrors": None}
    return JSONResponse(status_code=exc.status_code, content=body, headers=exc.headers)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    field_errors = {
        ".".join(str(part) for part in error["loc"][1:]): error["msg"]
        for error in exc.errors()
    }
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "fieldErrors": field_errors,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled request error")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"code": "INTERNAL_ERROR", "message": "Internal server error", "fieldErrors": None},
    )

app.include_router(applications_router, prefix="/api/v1", tags=["applications"])
app.include_router(assistant_router, prefix="/api/v1", tags=["assistant"])
app.include_router(bank_router, prefix="/api/v1", tags=["bank"])
app.include_router(catalog_router, prefix="/api/v1", tags=["catalog"])
app.include_router(mocks_router, prefix="/api/v1", tags=["mocks"])
app.include_router(notifications_router, prefix="/api/v1", tags=["notifications"])
app.include_router(profile_router, prefix="/api/v1", tags=["profile"])
app.include_router(recommendations_router, prefix="/api/v1", tags=["recommendations"])
app.include_router(system_router, prefix="/api/v1", tags=["system"])


Base.metadata.create_all(bind=engine)
