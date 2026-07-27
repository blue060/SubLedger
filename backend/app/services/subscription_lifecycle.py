from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models import Subscription


EXPIRING_WINDOW_DAYS = 30


def get_subscription_lifecycle(
    subscription: Subscription,
    as_of: date | None = None,
) -> str:
    """Return one consistent display state for a subscription."""
    as_of = as_of or date.today()
    expiry_date = subscription.expiry_date

    # An expiry date is inclusive: a subscription remains usable on that day.
    if expiry_date and expiry_date < as_of:
        return "expired"
    if not subscription.is_active:
        return "inactive"
    if subscription.billing_cycle == "permanent":
        return "permanent"
    if subscription.billing_cycle == "once":
        return "one_time"
    if expiry_date == as_of:
        return "expires_today"
    if expiry_date and expiry_date <= as_of + timedelta(days=EXPIRING_WINDOW_DAYS):
        return "expiring"
    if not subscription.auto_renew:
        return "ending"
    return "active"


def deactivate_expired_subscriptions(
    db: Session,
    as_of: date | None = None,
) -> int:
    """Deactivate subscriptions after their inclusive expiry date."""
    as_of = as_of or date.today()
    count = (
        db.query(Subscription)
        .filter(
            Subscription.is_active == True,
            Subscription.expiry_date != None,
            Subscription.expiry_date < as_of,
        )
        .update({Subscription.is_active: False}, synchronize_session=False)
    )
    if count:
        db.commit()
    return count
