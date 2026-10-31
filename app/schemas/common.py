from decimal import Decimal
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, StringConstraints


def _normalize_currency(value: Any) -> Any:
    return value.strip().upper() if isinstance(value, str) else value


CurrencyCode = Annotated[
    str, BeforeValidator(_normalize_currency), StringConstraints(pattern=r"^[A-Z]{3}$")
]
PositiveMoney = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]


class RequestModel(BaseModel):
    """Base for request bodies: unknown fields are rejected rather than silently ignored."""

    model_config = ConfigDict(extra="forbid")


class ORMModel(BaseModel):
    """Base for responses built from SQLAlchemy objects."""

    model_config = ConfigDict(from_attributes=True)


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[Any] | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
