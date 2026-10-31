from decimal import Decimal

from app.core.exceptions import NotFoundError
from app.models import Invoice, LedgerEntry, LedgerEntryType, PaymentAttempt
from app.repositories import CustomerRepository, LedgerRepository


class LedgerService:
    """Writes append-only financial events and reads a customer's history.

    Record methods never commit: they join the caller's transaction, so a ledger entry
    is persisted if and only if the business operation that produced it is persisted.
    """

    def __init__(self, ledger: LedgerRepository, customers: CustomerRepository) -> None:
        self.ledger = ledger
        self.customers = customers

    def record_invoice_created(self, invoice: Invoice) -> LedgerEntry:
        return self._append(
            customer_id=invoice.customer_id,
            invoice_id=invoice.id,
            entry_type=LedgerEntryType.INVOICE_CREATED,
            amount=invoice.amount_due,
            currency=invoice.currency,
            reference_id=f"invoice:{invoice.id}",
            description=(
                f"Invoice {invoice.id} issued for period "
                f"{invoice.period_start.isoformat()} to {invoice.period_end.isoformat()}."
            ),
        )

    def record_payment_success(self, payment: PaymentAttempt, invoice: Invoice) -> LedgerEntry:
        return self._append(
            customer_id=invoice.customer_id,
            invoice_id=invoice.id,
            entry_type=LedgerEntryType.PAYMENT_SUCCESS,
            amount=payment.amount,
            currency=payment.currency,
            reference_id=f"payment_attempt:{payment.id}",
            description=f"Payment {payment.id} applied to invoice {invoice.id}.",
        )

    def record_payment_failure(self, payment: PaymentAttempt, invoice: Invoice) -> LedgerEntry:
        return self._append(
            customer_id=invoice.customer_id,
            invoice_id=invoice.id,
            entry_type=LedgerEntryType.PAYMENT_FAILURE,
            amount=payment.amount,
            currency=payment.currency,
            reference_id=f"payment_attempt:{payment.id}",
            description=f"Payment {payment.id} for invoice {invoice.id} failed: {payment.failure_reason}",
        )

    def get_customer_ledger(self, customer_id: int, skip: int = 0, limit: int = 100) -> list[LedgerEntry]:
        if self.customers.get(customer_id) is None:
            raise NotFoundError(f"Customer {customer_id} not found.")
        return self.ledger.list_for_customer(customer_id, skip=skip, limit=limit)

    def _append(
        self,
        *,
        customer_id: int,
        invoice_id: int | None,
        entry_type: LedgerEntryType,
        amount: Decimal,
        currency: str,
        reference_id: str,
        description: str,
    ) -> LedgerEntry:
        entry = LedgerEntry(
            customer_id=customer_id,
            invoice_id=invoice_id,
            entry_type=entry_type,
            amount=amount,
            currency=currency,
            reference_id=reference_id,
            description=description,
        )
        return self.ledger.add(entry)
