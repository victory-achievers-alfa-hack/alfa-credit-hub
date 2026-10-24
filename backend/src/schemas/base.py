from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict
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
