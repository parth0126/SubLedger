from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.clock import utc_now
from app.db.base import Base
from app.models.enums import InvoiceStatus, db_enum

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.payment_attempt import PaymentAttempt
    from app.models.subscription import Subscription


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        CheckConstraint("amount_due > 0", name="ck_invoices_amount_due_positive"),
        CheckConstraint("amount_paid >= 0", name="ck_invoices_amount_paid_non_negative"),
        CheckConstraint("amount_paid <= amount_due", name="ck_invoices_amount_paid_within_due"),
        # One invoice per subscription billing period.
        UniqueConstraint("subscription_id", "period_start", name="uq_invoices_subscription_period"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    subscription_id: Mapped[int] = mapped_column(
        ForeignKey("subscriptions.id", ondelete="RESTRICT"), index=True
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), index=True
    )
    amount_due: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[InvoiceStatus] = mapped_column(
        db_enum(InvoiceStatus, "ck_invoices_status"), default=InvoiceStatus.DRAFT, index=True
    )
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    subscription: Mapped["Subscription"] = relationship(back_populates="invoices")
    customer: Mapped["Customer"] = relationship(back_populates="invoices")
    payment_attempts: Mapped[list["PaymentAttempt"]] = relationship(back_populates="invoice")

    @property
    def balance_due(self) -> Decimal:
        return self.amount_due - self.amount_paid
