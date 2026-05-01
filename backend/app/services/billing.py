from dateutil.relativedelta import relativedelta
from datetime import date


def calculate_next_payment_date(
    first_payment_date: date,
    billing_cycle: str,
    reference_date: date | None = None,
) -> date:
    if reference_date is None:
        reference_date = date.today()

    cycle_deltas = {
        "monthly": relativedelta(months=1),
        "quarterly": relativedelta(months=3),
        "yearly": relativedelta(years=1),
    }
    delta = cycle_deltas.get(billing_cycle)
    if delta is None:
        raise ValueError(f"未知的计费周期: {billing_cycle}")

    next_date = first_payment_date
    while next_date < reference_date:
        next_date = next_date + delta
    return next_date


def calculate_monthly_projection(
    subscription,
    target_month: date,
) -> float | None:
    """Return the amount this subscription costs in the given month, or None if not charged."""
    first = subscription.first_payment_date
    cycle = subscription.billing_cycle
    next_pay = subscription.next_payment_date

    if target_month.year < first.year or (target_month.year == first.year and target_month.month < first.month):
        return None

    if cycle == "monthly":
        return subscription.amount

    # For quarterly/yearly, check if a payment falls in this month
    cycle_deltas = {
        "quarterly": relativedelta(months=3),
        "yearly": relativedelta(years=1),
    }
    delta = cycle_deltas[cycle]

    d = first
    while d < target_month.replace(day=1):
        d = d + delta

    if d.year == target_month.year and d.month == target_month.month:
        return subscription.amount

    # Also check if next_payment_date falls in this month
    if next_pay.year == target_month.year and next_pay.month == target_month.month:
        return subscription.amount

    return None