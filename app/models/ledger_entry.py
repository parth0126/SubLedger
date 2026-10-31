from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text, event
from sqlalchemy.orm import Mapped, mapped_column

from app.core.clock import utc_now
from app.core.exceptions import AppendOnlyViolation
from app.db.base import Base
from app.models.enums import LedgerEntryType, db_enum


class LedgerEntry(Base):
    """Immutable financial event. Rows are only ever inserted (see listeners below)."""

    __tablename__ = "ledger_entries"
    __table_args__ = (
        Index("ix_ledger_entries_customer_id_created_at", "customer_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"))
    invoice_id: Mapped[int | None] = mapped_column(
        ForeignKey("invoices.id", ondelete="RESTRICT"), index=True
    )
    entry_type: Mapped[LedgerEntryType] = mapped_column(
        db_enum(LedgerEntryType, "ck_ledger_entries_entry_type")
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))
    # Points at the record that caused the entry, e.g. "invoice:12" or "payment_attempt:40".
    reference_id: Mapped[str] = mapped_column(String(64), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


@event.listens_for(LedgerEntry, "before_update")
def _prevent_ledger_update(mapper, connection, target: LedgerEntry) -> None:
    raise AppendOnlyViolation("Ledger entries are append-only and cannot be modified.")


@event.listens_for(LedgerEntry, "before_delete")
def _prevent_ledger_delete(mapper, connection, target: LedgerEntry) -> None:
    raise AppendOnlyViolation("Ledger entries are append-only and cannot be deleted.")
