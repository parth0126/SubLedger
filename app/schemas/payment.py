from pydantic import Field, model_validator

from app.models.enums import PaymentStatus
from app.schemas.common import CurrencyCode, ORMModel, PositiveMoney, RequestModel
from app.schemas.invoice import InvoicePaymentSummary, InvoiceResponse


class PaymentRecord(RequestModel):
    invoice_id: int = Field(gt=0)
    amount: PositiveMoney
    currency: CurrencyCode | None = Field(default=None, description="Defaults to the invoice currency.")
    status: PaymentStatus
    provider_reference: str | None = Field(default=None, max_length=255)
    failure_reason: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def _check_failure_reason(self) -> "PaymentRecord":
        if self.status is PaymentStatus.FAILED and not (self.failure_reason or "").strip():
            raise ValueError("failure_reason is required for failed payments")
        if self.status is PaymentStatus.SUCCESS and self.failure_reason is not None:
            raise ValueError("failure_reason must be omitted for successful payments")
        return self


class PaymentAttemptResponse(InvoicePaymentSummary):
    invoice_id: int


class PaymentRecordResponse(ORMModel):
    payment: PaymentAttemptResponse
    invoice: InvoiceResponse
