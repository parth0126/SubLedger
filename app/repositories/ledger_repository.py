from sqlalchemy import select

from app.models import LedgerEntry
from app.repositories.base import BaseRepository


class LedgerRepository(BaseRepository[LedgerEntry]):
    """Append-only: exposes insert and read operations, nothing that updates or deletes."""

    model = LedgerEntry

    def list_for_customer(self, customer_id: int, skip: int = 0, limit: int = 100) -> list[LedgerEntry]:
        stmt = (
            select(LedgerEntry)
            .where(LedgerEntry.customer_id == customer_id)
            .order_by(LedgerEntry.created_at, LedgerEntry.id)
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.scalars(stmt))
