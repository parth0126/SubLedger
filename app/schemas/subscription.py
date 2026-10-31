from datetime import date, datetime

from pydantic import Field

from app.models.enums import SubscriptionStatus
from app.schemas.common import ORMModel, RequestModel


class SubscriptionCreate(RequestModel):
    customer_id: int = Field(gt=0)
    plan_id: int = Field(gt=0)
    start_date: date | None = Field(default=None, description="Defaults to today (UTC).")


class SubscriptionResponse(ORMModel):
    id: int
    customer_id: int
    plan_id: int
    status: SubscriptionStatus
    start_date: date
    current_period_start: date
    current_period_end: date
    cancelled_at: datetime | None
    created_at: datetime
