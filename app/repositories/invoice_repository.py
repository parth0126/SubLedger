from datetime import date

from sqlalchemy import exists, select

from app.models import Invoice
from app.repositories.base import BaseRepository


class InvoiceRepository(BaseRepository[Invoice]):
    model = Invoice

    def exists_for_period(self, subscription_id: int, period_start: date) -> bool:
        stmt = select(
            exists().where(
                Invoice.subscription_id == subscription_id,
                Invoice.period_start == period_start,
            )
        )
        return bool(self.session.scalar(stmt))
