"""Pure date arithmetic for billing periods (no I/O, easy to unit test)."""

import calendar
from datetime import date

from app.models.enums import BillingCycle

_MONTHS_PER_CYCLE = {
    BillingCycle.MONTHLY: 1,
    BillingCycle.QUARTERLY: 3,
    BillingCycle.YEARLY: 12,
}


def add_months(value: date, months: int) -> date:
    """Add months, clamping the day to the target month's length (Jan 31 + 1 month -> Feb 28/29)."""
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def period_end(period_start: date, cycle: BillingCycle) -> date:
    """Exclusive end of the billing period that starts on `period_start`."""
    return add_months(period_start, _MONTHS_PER_CYCLE[cycle])
