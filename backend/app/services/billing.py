from dateutil.relativedelta import relativedelta
from datetime import date


RECURRING_CYCLES = ("monthly", "quarterly", "yearly", "custom")


def get_billing_delta(
    billing_cycle: str,
    billing_cycle_num: int = 1,
    billing_cycle_unit: str = "month",
):
    """Return the calendar delta for a recurring billing cycle."""
    if billing_cycle == "monthly":
        return relativedelta(months=1)
    if billing_cycle == "quarterly":
        return relativedelta(months=3)
    if billing_cycle == "yearly":
        return relativedelta(years=1)
    if billing_cycle == "custom":
        if billing_cycle_unit == "year":
            return relativedelta(years=billing_cycle_num)
        return relativedelta(months=billing_cycle_num)
    raise ValueError(f"未知的计费周期: {billing_cycle}")


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
    if billing_cycle in ("once", "permanent"):
        return first_payment_date

    delta = get_billing_delta(billing_cycle, billing_cycle_num, billing_cycle_unit)

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
    expiry_date = getattr(subscription, "expiry_date", None)
    if expiry_date:
        last_month = expiry_date.replace(day=1)
        if target_month > last_month:
            return None

    if target_month.year < first.year or (target_month.year == first.year and target_month.month < first.month):
        return None

    # One-time / Permanent: only charged in the first payment month
    if cycle in ("once", "permanent"):
        if target_month.year == first.year and target_month.month == first.month:
            return _effective_amount(subscription, first, target_month)
        return None

    num = getattr(subscription, 'billing_cycle_num', 1) or 1
    unit = getattr(subscription, 'billing_cycle_unit', 'month') or 'month'
    delta = get_billing_delta(cycle, num, unit)

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
        intro_end = first + relativedelta(months=intro_months)
        month_start = target_month
        month_end = target_month + relativedelta(months=1)

        # Entire month within intro period
        if intro_end >= month_end:
            return intro_amount

        # Entire month after intro period
        if intro_end <= month_start:
            return subscription.amount

        # Month straddles the intro boundary — prorate by days
        intro_days = (intro_end - month_start).days
        full_price_days = (month_end - intro_end).days
        total_days = (month_end - month_start).days
        return round(intro_amount * intro_days / total_days + subscription.amount * full_price_days / total_days, 2)

    return subscription.amount
