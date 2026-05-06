from dateutil.relativedelta import relativedelta
from datetime import date


def calculate_next_payment_date(
    first_payment_date: date,
    billing_cycle: str,
    reference_date: date | None = None,
    billing_cycle_num: int = 1,
    billing_cycle_unit: str = "month",
) -> date | None:
    """Calculate the next payment date. Returns None for 'once' type."""
    if reference_date is None:
        reference_date = date.today()

    # Permanent/one-time: next payment is the first payment date itself
    if billing_cycle == "once":
        return first_payment_date

    # Built-in cycles
    if billing_cycle == "monthly":
        delta = relativedelta(months=1)
    elif billing_cycle == "quarterly":
        delta = relativedelta(months=3)
    elif billing_cycle == "yearly":
        delta = relativedelta(years=1)
    elif billing_cycle == "custom":
        if billing_cycle_unit == "year":
            delta = relativedelta(years=billing_cycle_num)
        else:
            delta = relativedelta(months=billing_cycle_num)
    else:
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

    # Check if subscription has expired before this month
    if subscription.expiry_date:
        last_month = subscription.expiry_date.replace(day=1)
        if target_month > last_month:
            return None

    if target_month.year < first.year or (target_month.year == first.year and target_month.month < first.month):
        return None

    # One-time: only charged in the first payment month
    if cycle == "once":
        if target_month.year == first.year and target_month.month == first.month:
            return _effective_amount(subscription, first, target_month)
        return None

    # Determine the cycle delta
    if cycle == "monthly":
        delta = relativedelta(months=1)
    elif cycle == "quarterly":
        delta = relativedelta(months=3)
    elif cycle == "yearly":
        delta = relativedelta(years=1)
    elif cycle == "custom":
        num = getattr(subscription, 'billing_cycle_num', 1) or 1
        unit = getattr(subscription, 'billing_cycle_unit', 'month') or 'month'
        if unit == "year":
            delta = relativedelta(years=num)
        else:
            delta = relativedelta(months=num)
    else:
        raise ValueError(f"Unknown billing cycle: {cycle}")

    d = first
    while d < target_month.replace(day=1):
        d = d + delta

    if d.year == target_month.year and d.month == target_month.month:
        return _effective_amount(subscription, d, target_month)

    if next_pay and next_pay.year == target_month.year and next_pay.month == target_month.month:
        return _effective_amount(subscription, next_pay, target_month)

    return None


def _effective_amount(subscription, payment_date: date, target_month: date) -> float:
    """Return the effective amount for a subscription in a given month, considering intro pricing."""
    intro_amount = getattr(subscription, 'intro_amount', None)
    intro_months = getattr(subscription, 'intro_months', None)

    if intro_amount is not None and intro_months is not None and intro_months > 0:
        first = subscription.first_payment_date
        months_since_start = (target_month.year - first.year) * 12 + (target_month.month - first.month)
        if months_since_start < intro_months:
            return intro_amount

    return subscription.amount