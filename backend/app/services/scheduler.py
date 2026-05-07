import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.database import SessionLocal
from app.models import Subscription
from app.services.notifier import check_upcoming_subscriptions
from app.services.billing import calculate_next_payment_date

logger = logging.getLogger("subledger")

scheduler = AsyncIOScheduler()


async def daily_check_job():
    logger.info("开始检查即将到期的订阅...")
    db = SessionLocal()
    try:
        await check_upcoming_subscriptions(db)
        _advance_overdue_payment_dates(db)
    except Exception as e:
        logger.error(f"订阅检查任务失败: {e}")
    finally:
        db.close()
    logger.info("订阅检查完成")


def _advance_overdue_payment_dates(db):
    from datetime import date
    today = date.today()
    subs = (
        db.query(Subscription)
        .filter(
            Subscription.is_active == True,
            Subscription.next_payment_date != None,
            Subscription.next_payment_date < today,
            Subscription.billing_cycle.notin_(["once", "permanent"]),
        )
        .all()
    )
    updated = 0
    for sub in subs:
        new_date = calculate_next_payment_date(
            sub.first_payment_date,
            sub.billing_cycle,
            reference_date=today,
            billing_cycle_num=sub.billing_cycle_num or 1,
            billing_cycle_unit=sub.billing_cycle_unit or "month",
        )
        if new_date and new_date != sub.next_payment_date:
            sub.next_payment_date = new_date
            updated += 1
    if updated:
        db.commit()
        logger.info(f"自动推进了 {updated} 个订阅的下次付款日期")


def start_scheduler():
    scheduler.add_job(
        daily_check_job,
        "cron",
        hour=0,
        minute=0,
        id="daily_subscription_check",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("定时任务已启动")


def stop_scheduler():
    scheduler.shutdown()
    logger.info("定时任务已停止")