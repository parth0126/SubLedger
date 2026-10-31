from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.clock import utc_now
from app.db.base import Base
from app.models.enums import SubscriptionStatus, db_enum

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.invoice import Invoice
    from app.models.plan import Plan

_ACTIVE_ONLY = text("status = 'active'")


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        CheckConstraint(
            "current_period_end > current_period_start", name="ck_subscriptions_period_order"
        ),
        # Rule: a customer can hold at most one *active* subscription per plan.
        Index(
            "uq_subscriptions_active_customer_plan",
            "customer_id",
            "plan_id",
            unique=True,
            postgresql_where=_ACTIVE_ONLY,
            sqlite_where=_ACTIVE_ONLY,
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), index=True
    )
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id", ondelete="RESTRICT"), index=True)
    status: Mapped[SubscriptionStatus] = mapped_column(
        db_enum(SubscriptionStatus, "ck_subscriptions_status"),
        default=SubscriptionStatus.ACTIVE,
        index=True,
    )
    start_date: Mapped[date] = mapped_column(Date)
    # Billing periods are half-open: [current_period_start, current_period_end).
    current_period_start: Mapped[date] = mapped_column(Date)
    current_period_end: Mapped[date] = mapped_column(Date)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    customer: Mapped["Customer"] = relationship(back_populates="subscriptions")
    plan: Mapped["Plan"] = relationship(back_populates="subscriptions")
    invoices: Mapped[list["Invoice"]] = relationship(back_populates="subscription")
