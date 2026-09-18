from calendar import monthrange
from datetime import date, timedelta


def add_billing_cycle(start_date: date, cycle_value: int, cycle_unit: str) -> date:
    """Advance a date by a billing cycle without approximating months or years."""
    if cycle_value < 1:
        raise ValueError("cycle_value must be at least 1")

    if cycle_unit == "day":
        return start_date + timedelta(days=cycle_value)

    if cycle_unit == "week":
        return start_date + timedelta(weeks=cycle_value)

    if cycle_unit not in {"month", "year"}:
        raise ValueError("Unsupported cycle_unit")

    months_to_add = cycle_value if cycle_unit == "month" else cycle_value * 12
    target_month_index = start_date.month - 1 + months_to_add
    target_year = start_date.year + target_month_index // 12
    target_month = target_month_index % 12 + 1
    target_day = min(start_date.day, monthrange(target_year, target_month)[1])

    return date(target_year, target_month, target_day)
