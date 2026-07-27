from datetime import date, timedelta

from app.models import Subscription
from app.services.subscription_lifecycle import (
    deactivate_expired_subscriptions,
    get_subscription_lifecycle,
)


def _subscription(**overrides):
    values = {
        "name": "状态测试",
        "user_id": 1,
        "amount": 10,
        "currency": "CNY",
        "billing_cycle": "monthly",
        "first_payment_date": date(2026, 1, 1),
        "auto_renew": True,
        "is_active": True,
    }
    values.update(overrides)
    return Subscription(**values)


def test_expiry_date_is_inclusive():
    today = date(2026, 7, 27)
    sub = _subscription(expiry_date=today)

    assert get_subscription_lifecycle(sub, today) == "expires_today"
    assert get_subscription_lifecycle(sub, today + timedelta(days=1)) == "expired"


def test_lifecycle_distinguishes_expiring_inactive_and_permanent():
    today = date(2026, 7, 27)
    assert get_subscription_lifecycle(
        _subscription(expiry_date=today + timedelta(days=7)), today
    ) == "expiring"
    assert get_subscription_lifecycle(_subscription(is_active=False), today) == "inactive"
    assert get_subscription_lifecycle(
        _subscription(billing_cycle="permanent", auto_renew=False), today
    ) == "permanent"


def test_expired_subscriptions_are_deactivated(db):
    today = date(2026, 7, 27)
    expired = _subscription(expiry_date=today - timedelta(days=1))
    due_today = _subscription(name="今天到期", expiry_date=today)
    db.add_all([expired, due_today])
    db.commit()

    assert deactivate_expired_subscriptions(db, today) == 1
    db.refresh(expired)
    db.refresh(due_today)
    assert expired.is_active is False
    assert due_today.is_active is True
