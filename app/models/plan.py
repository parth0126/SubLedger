from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.clock import utc_now
from app.db.base import Base
from app.models.enums import BillingCycle, PlanStatus, db_enum

if TYPE_CHECKING:
    from app.models.subscription import Subscription


class Plan(Base):
    __tablename__ = "plans"
    __table_args__ = (CheckConstraint("price > 0", name="ck_plans_price_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)
    billing_cycle: Mapped[BillingCycle] = mapped_column(db_enum(BillingCycle, "ck_plans_billing_cycle"))
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[PlanStatus] = mapped_column(
        db_enum(PlanStatus, "ck_plans_status"), default=PlanStatus.ACTIVE, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="plan")
