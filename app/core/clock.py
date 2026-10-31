"""Single source of "now" so all timestamps and billing dates are in UTC."""

from datetime import UTC, date, datetime


def utc_now() -> datetime:
    return datetime.now(UTC)


def utc_today() -> date:
    return utc_now().date()
