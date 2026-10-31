from datetime import timedelta
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.clock import utc_today
from app.core.exceptions import BusinessRuleViolation, ConflictError, NotFoundError
from app.db.session import transaction
from app.models import Invoice, InvoiceStatus, Subscription, SubscriptionStatus
from app.repositories import InvoiceRepository, SubscriptionRepository
from app.schemas.invoice import InvoiceGenerate
from app.services.billing_period import period_end
from app.services.ledger_service import LedgerService

# Unpaid invoices in these states become `overdue` once their due date has passed.
_OVERDUE_ELIGIBLE = frozenset({InvoiceStatus.ISSUED, InvoiceStatus.PARTIALLY_PAID})


class InvoiceService:
    """Generates invoices for subscription billing periods and serves invoice details."""

    def __init__(
        self,
        session: Session,
        invoices: InvoiceRepository,
        subscriptions: SubscriptionRepository,
        ledger: LedgerService,
        due_days: int,
    ) -> None:
        self.session = session
        self.invoices = invoices
        self.subscriptions = subscriptions
        self.ledger = ledger
        self.due_days = due_days

    def generate_invoice(self, data: InvoiceGenerate) -> Invoice:
        """Invoice the subscription's current billing period at the plan's *current* price.

        If the current period is already invoiced and has ended, the subscription is
        renewed into the next period and that period is invoiced instead.
        """
        try:
            with transaction(self.session):
                subscription = self.subscriptions.get_for_update(data.subscription_id)
                if subscription is None:
                    raise NotFoundError(f"Subscription {data.subscription_id} not found.")
                if subscription.status != SubscriptionStatus.ACTIVE:
                    raise BusinessRuleViolation("Invoices can only be generated for active subscriptions.")

                if self.invoices.exists_for_period(subscription.id, subscription.current_period_start):
                    if subscription.current_period_end > utc_today():
                        raise ConflictError(
                            "The current billing period of this subscription is already invoiced."
                        )
                    self._advance_period(subscription)

                plan = subscription.plan
                invoice = Invoice(
                    subscription_id=subscription.id,
                    customer_id=subscription.customer_id,
                    amount_due=plan.price,  # snapshot of the price at generation time
                    amount_paid=Decimal("0.00"),
                    currency=plan.currency,
                    status=InvoiceStatus.ISSUED,
                    period_start=subscription.current_period_start,
                    period_end=subscription.current_period_end,
                    due_date=utc_today() + timedelta(days=self.due_days),
                )
                self.invoices.add(invoice)
                self.ledger.record_invoice_created(invoice)
        except IntegrityError as exc:  # unique (subscription_id, period_start) caught a race
            raise ConflictError("An invoice already exists for this billing period.") from exc
        return invoice

    def get_invoice(self, invoice_id: int) -> Invoice:
        invoice = self.invoices.get(invoice_id)
        if invoice is None:
            raise NotFoundError(f"Invoice {invoice_id} not found.")
        if invoice.status in _OVERDUE_ELIGIBLE and invoice.due_date < utc_today():
            with transaction(self.session):
                invoice.status = InvoiceStatus.OVERDUE
        return invoice

    @staticmethod
    def _advance_period(subscription: Subscription) -> None:
        start = subscription.current_period_end
        subscription.current_period_start = start
        subscription.current_period_end = period_end(start, subscription.plan.billing_cycle)
