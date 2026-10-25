from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic.functional_serializers import PlainSerializer

JsonDecimal = Annotated[
    Decimal,
    PlainSerializer(float, return_type=float, when_used="json"),
]


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class ApiSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
        from_attributes=True,
    )

    @field_validator("*", mode="after")
    @classmethod
    def normalize_utc_timestamps(cls, value):
        # Persistence stores UTC; SQLite drops timezone metadata on DateTime reads.
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        return value
