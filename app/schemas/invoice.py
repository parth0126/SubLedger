from datetime import date, datetime
from decimal import Decimal

from pydantic import Field

from app.models.enums import InvoiceStatus, PaymentStatus
from app.schemas.common import ORMModel, RequestModel


class InvoiceGenerate(RequestModel):
    subscription_id: int = Field(gt=0)


class InvoiceResponse(ORMModel):
    id: int
    subscription_id: int
    customer_id: int
    amount_due: Decimal
    amount_paid: Decimal
    balance_due: Decimal
    currency: str
    status: InvoiceStatus
    period_start: date
    period_end: date
    due_date: date
    created_at: datetime


class InvoicePaymentSummary(ORMModel):
    id: int
    amount: Decimal
    currency: str
    status: PaymentStatus
    provider_reference: str | None
    failure_reason: str | None
    created_at: datetime


class InvoiceDetailResponse(InvoiceResponse):
    payment_attempts: list[InvoicePaymentSummary]
