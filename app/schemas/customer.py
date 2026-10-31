from datetime import datetime
from typing import Any

from pydantic import EmailStr, Field

from app.schemas.common import ORMModel, RequestModel


class CustomerCreate(RequestModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    company: str | None = Field(default=None, max_length=255)
    contact_details: dict[str, Any] | None = None


class CustomerResponse(ORMModel):
    id: int
    name: str
    email: str
    company: str | None
    contact_details: dict[str, Any] | None
    created_at: datetime
