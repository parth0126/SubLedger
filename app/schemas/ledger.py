from datetime import datetime
from decimal import Decimal

from app.models.enums import LedgerEntryType
from app.schemas.common import ORMModel


class LedgerEntryResponse(ORMModel):
    id: int
    customer_id: int
    invoice_id: int | None
    entry_type: LedgerEntryType
    amount: Decimal
    currency: str
    reference_id: str
    description: str | None
    created_at: datetime
