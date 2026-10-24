import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


logger = logging.getLogger(__name__)


async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        body = {"fieldErrors": None, **detail}
    else:
        body = {
            "code": "HTTP_ERROR",
            "message": str(detail),
            "fieldErrors": None,
        }
    return JSONResponse(status_code=exc.status_code, content=body, headers=exc.headers)


async def handle_validation_exception(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
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


async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled request error")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": "INTERNAL_ERROR",
            "message": "Internal server error",
            "fieldErrors": None,
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register API-wide handlers on the application, not on a versioned router."""
    app.add_exception_handler(HTTPException, handle_http_exception)
    app.add_exception_handler(RequestValidationError, handle_validation_exception)
    app.add_exception_handler(Exception, handle_unexpected_exception)
