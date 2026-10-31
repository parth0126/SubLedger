from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleViolation, NotFoundError
from app.db.session import transaction
from app.models import Invoice, InvoiceStatus, PaymentAttempt, PaymentStatus
from app.repositories import InvoiceRepository, PaymentAttemptRepository
from app.schemas.payment import PaymentRecord
from app.services.ledger_service import LedgerService

_PAYABLE_STATUSES = frozenset(
    {InvoiceStatus.ISSUED, InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.OVERDUE}
)


@dataclass(frozen=True)
class PaymentResult:
    payment: PaymentAttempt
    invoice: Invoice


class PaymentService:
    """Records payment attempts against invoices and keeps invoice balances consistent."""

    def __init__(
        self,
        session: Session,
        invoices: InvoiceRepository,
        payments: PaymentAttemptRepository,
        ledger: LedgerService,
    ) -> None:
        self.session = session
        self.invoices = invoices
        self.payments = payments
        self.ledger = ledger

    def record_payment(self, data: PaymentRecord) -> PaymentResult:
        """Persist the attempt, the invoice update and the ledger entry atomically.

        The invoice row is locked so concurrent payments cannot overpay it.
        """
        with transaction(self.session):
            invoice = self.invoices.get_for_update(data.invoice_id)
            if invoice is None:
                raise NotFoundError(f"Invoice {data.invoice_id} not found.")
            currency = data.currency or invoice.currency
            self._validate(invoice, data, currency)

            payment = PaymentAttempt(
                invoice_id=invoice.id,
                amount=data.amount,
                currency=currency,
                status=data.status,
                provider_reference=data.provider_reference,
                failure_reason=data.failure_reason if data.status is PaymentStatus.FAILED else None,
            )
            self.payments.add(payment)

            if data.status is PaymentStatus.SUCCESS:
                invoice.amount_paid += data.amount
                invoice.status = (
                    InvoiceStatus.PAID
                    if invoice.amount_paid == invoice.amount_due
                    else InvoiceStatus.PARTIALLY_PAID
                )
                self.ledger.record_payment_success(payment, invoice)
            else:
                # Failed attempts are recorded for audit but never change amount_paid.
                self.ledger.record_payment_failure(payment, invoice)

        return PaymentResult(payment=payment, invoice=invoice)

    @staticmethod
    def _validate(invoice: Invoice, data: PaymentRecord, currency: str) -> None:
        if invoice.status not in _PAYABLE_STATUSES:
            raise BusinessRuleViolation(
                f"Invoice {invoice.id} is '{invoice.status.value}' and cannot accept payments."
            )
        if data.amount <= 0:
            raise BusinessRuleViolation("Payment amount must be greater than zero.")
        if currency != invoice.currency:
            raise BusinessRuleViolation(
                f"Payment currency {currency} does not match invoice currency {invoice.currency}."
            )
        if data.status is PaymentStatus.SUCCESS and data.amount > invoice.balance_due:
            raise BusinessRuleViolation(
                f"Payment amount {data.amount} exceeds the remaining invoice balance "
                f"{invoice.balance_due}."
            )
