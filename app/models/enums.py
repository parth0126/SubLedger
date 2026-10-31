"""Domain enumerations and the column type used to persist them."""

from enum import StrEnum

from sqlalchemy import Enum as SAEnum


class BillingCycle(StrEnum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class PlanStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class SubscriptionStatus(StrEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"


class InvoiceStatus(StrEnum):
    DRAFT = "draft"
    ISSUED = "issued"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    VOID = "void"


class PaymentStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"


class LedgerEntryType(StrEnum):
    INVOICE_CREATED = "invoice_created"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILURE = "payment_failure"


def db_enum(enum_cls: type[StrEnum], name: str) -> SAEnum:
    """Store enum *values* as VARCHAR guarded by a CHECK constraint (portable, easy to migrate)."""
    return SAEnum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=32,
        validate_strings=True,
        values_callable=lambda members: [member.value for member in members],
    )
