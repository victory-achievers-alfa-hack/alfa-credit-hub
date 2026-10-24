from .base import ApiSchema


class ErrorResponse(ApiSchema):
    code: str
    message: str
    field_errors: dict[str, str] | None = None
