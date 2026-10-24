from pydantic import BaseModel, Field


class StatusMessageResponse(BaseModel):
    status: dict = {200: "OK"}
    message: str = Field(
        ...,
        examples=["Демо-данные успешно сброшены к начальному состоянию"],
        max_length=255,
    )


class HealthCheckResponse(BaseModel):
    status: dict = {200: "OK"}
    description: str | None = Field(default=None, max_length=255)
