from datetime import datetime
from decimal import Decimal

from pydantic import Field, model_validator

from app.models.enums import BillingCycle, PlanStatus
from app.schemas.common import CurrencyCode, ORMModel, PositiveMoney, RequestModel


class PlanCreate(RequestModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    billing_cycle: BillingCycle
    price: PositiveMoney
    currency: CurrencyCode = "USD"
    status: PlanStatus = PlanStatus.ACTIVE


class PlanUpdate(RequestModel):
    """Partial update. billing_cycle and currency are immutable because existing
    subscriptions and invoices depend on them."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    price: PositiveMoney | None = None
    status: PlanStatus | None = None

    @model_validator(mode="after")
    def _reject_null_for_required_fields(self) -> "PlanUpdate":
        for field in ("name", "price", "status"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"'{field}' cannot be null")
        return self


class PlanResponse(ORMModel):
    id: int
    name: str
    description: str | None
    billing_cycle: BillingCycle
    price: Decimal
    currency: str
    status: PlanStatus
    created_at: datetime
    updated_at: datetime
