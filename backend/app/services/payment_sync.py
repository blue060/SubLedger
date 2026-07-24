import logging
from datetime import date
from threading import Lock

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import PaymentRecord, Subscription
from app.services.billing import RECURRING_CYCLES, _effective_amount, calculate_next_payment_date, get_billing_delta

logger = logging.getLogger("subledger")
_sync_lock = Lock()


def sync_due_payments(db: Session, as_of: date | None = None) -> int:
    """Create missing due records and move recurring subscriptions past ``as_of``.

    The operation is idempotent: an existing record for the same subscription and
    scheduled payment date is reused, regardless of its status.
    """
    as_of = as_of or date.today()
    created = 0
    advanced = 0

    with _sync_lock:
        subscriptions = (
            db.query(Subscription)
            .filter(
                Subscription.is_active == True,
                Subscription.auto_renew == True,
                Subscription.billing_cycle.in_(RECURRING_CYCLES),
                or_(Subscription.next_payment_date == None, Subscription.next_payment_date <= as_of),
            )
            .all()
        )

        for sub in subscriptions:
            due_date = sub.next_payment_date
            if due_date is None:
                due_date = calculate_next_payment_date(
                    sub.first_payment_date,
                    sub.billing_cycle,
                    reference_date=as_of,
                    billing_cycle_num=sub.billing_cycle_num or 1,
                    billing_cycle_unit=sub.billing_cycle_unit or "month",
                )

            if due_date is None or due_date > as_of:
                if sub.next_payment_date != due_date:
                    sub.next_payment_date = due_date
                    advanced += 1
                continue

            delta = get_billing_delta(
                sub.billing_cycle,
                sub.billing_cycle_num or 1,
                sub.billing_cycle_unit or "month",
            )
            existing_dates = {
                row[0]
                for row in db.query(PaymentRecord.payment_date)
                .filter(
                    PaymentRecord.subscription_id == sub.id,
                    PaymentRecord.payment_date >= due_date,
                    PaymentRecord.payment_date <= as_of,
                )
                .all()
            }

            while due_date <= as_of:
                if due_date not in existing_dates:
                    db.add(PaymentRecord(
                        subscription_id=sub.id,
                        amount=_effective_amount(sub, due_date, due_date.replace(day=1)),
                        currency=sub.currency,
                        payment_date=due_date,
                        status="pending",
                    ))
                    created += 1
                due_date = due_date + delta

            if sub.next_payment_date != due_date:
                sub.next_payment_date = due_date
                advanced += 1

        if created or advanced:
            db.commit()
            logger.info("账期同步完成: 新增 %s 条待确认付款，推进 %s 个订阅", created, advanced)

    return created
