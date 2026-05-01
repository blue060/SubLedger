import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date
import pytest


def test_monthly_projection():
    from app.services.billing import calculate_monthly_projection

    class FakeSub:
        name = "test"
        amount = 10.0
        currency = "CNY"
        billing_cycle = "monthly"
        first_payment_date = date(2024, 1, 15)
        next_payment_date = date(2024, 6, 15)

    sub = FakeSub()
    result = calculate_monthly_projection(sub, date(2024, 6, 1))
    assert result == 10.0

    result = calculate_monthly_projection(sub, date(2023, 12, 1))
    assert result is None


def test_yearly_projection():
    from app.services.billing import calculate_monthly_projection

    class FakeSub:
        name = "test"
        amount = 120.0
        currency = "CNY"
        billing_cycle = "yearly"
        first_payment_date = date(2024, 3, 15)
        next_payment_date = date(2025, 3, 15)

    sub = FakeSub()
    # March should have the payment
    result = calculate_monthly_projection(sub, date(2025, 3, 1))
    assert result == 120.0

    # April should not
    result = calculate_monthly_projection(sub, date(2025, 4, 1))
    assert result is None