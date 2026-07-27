from datetime import date

from dateutil.relativedelta import relativedelta

from app.models import PaymentRecord, Subscription
from app.services.payment_sync import sync_due_payments


def _subscription(**overrides):
    data = {
        "name": "测试月付服务",
        "user_id": 1,
        "amount": 20.0,
        "currency": "CNY",
        "billing_cycle": "monthly",
        "billing_cycle_num": 1,
        "billing_cycle_unit": "month",
        "first_payment_date": date(2026, 1, 15),
        "next_payment_date": date(2026, 6, 15),
        "auto_renew": True,
        "is_active": True,
    }
    data.update(overrides)
    return Subscription(**data)


def test_sync_creates_every_missed_payment_and_advances_date(db):
    sub = _subscription()
    db.add(sub)
    db.commit()

    created = sync_due_payments(db, as_of=date(2026, 7, 24))
    db.refresh(sub)

    assert created == 2
    assert sub.next_payment_date == date(2026, 8, 15)
    records = db.query(PaymentRecord).order_by(PaymentRecord.payment_date).all()
    assert [record.payment_date for record in records] == [date(2026, 6, 15), date(2026, 7, 15)]
    assert all(record.status == "pending" for record in records)

    assert sync_due_payments(db, as_of=date(2026, 7, 24)) == 0
    assert db.query(PaymentRecord).count() == 2


def test_sync_reuses_existing_confirmed_record(db):
    sub = _subscription()
    db.add(sub)
    db.flush()
    db.add(PaymentRecord(
        subscription_id=sub.id,
        amount=20,
        currency="CNY",
        payment_date=date(2026, 6, 15),
        status="confirmed",
    ))
    db.commit()

    assert sync_due_payments(db, as_of=date(2026, 7, 24)) == 1
    assert db.query(PaymentRecord).count() == 2
    june = db.query(PaymentRecord).filter(PaymentRecord.payment_date == date(2026, 6, 15)).one()
    assert june.status == "confirmed"


def test_payment_list_syncs_due_records_and_returns_total(auth_client, db):
    today = date.today()
    sub = _subscription(first_payment_date=today, next_payment_date=today)
    db.add(sub)
    db.commit()

    response = auth_client.get("/api/payments?page=1&page_size=20")
    assert response.status_code == 200
    assert response.headers["x-total-count"] == "1"
    assert len(response.json()) == 1
    db.refresh(sub)
    assert sub.next_payment_date == today + relativedelta(months=1)
