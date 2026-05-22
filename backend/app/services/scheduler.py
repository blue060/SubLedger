import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.database import SessionLocal
from app.models import Subscription, PaymentRecord, AppSettings
from app.services.notifier import check_upcoming_subscriptions
from app.services.billing import calculate_next_payment_date
from app.services.backup import perform_backup

logger = logging.getLogger("subledger")

scheduler = AsyncIOScheduler()


async def daily_check_job():
    logger.info("开始检查即将到期的订阅...")
    db = SessionLocal()
    try:
        await check_upcoming_subscriptions(db)
        _advance_overdue_payment_dates(db)
        _auto_disable_expired(db)
        await _check_budget_alert(db)
    except Exception as e:
        logger.error(f"订阅检查任务失败: {e}")
    finally:
        db.close()
    logger.info("订阅检查完成")


def backup_job():
    logger.info("开始自动备份...")
    db = SessionLocal()
    try:
        perform_backup(db)
    except Exception as e:
        logger.error(f"自动备份失败: {e}")
    finally:
        db.close()


def _advance_overdue_payment_dates(db):
    from datetime import date
    today = date.today()
    subs = (
        db.query(Subscription)
        .filter(
            Subscription.is_active == True,
            Subscription.auto_renew == True,
            Subscription.next_payment_date != None,
            Subscription.next_payment_date < today,
            Subscription.billing_cycle.notin_(["once", "permanent"]),
        )
        .all()
    )
    updated = 0
    for sub in subs:
        old_date = sub.next_payment_date
        new_date = calculate_next_payment_date(
            sub.first_payment_date,
            sub.billing_cycle,
            reference_date=today,
            billing_cycle_num=sub.billing_cycle_num or 1,
            billing_cycle_unit=sub.billing_cycle_unit or "month",
        )
        if new_date and new_date != old_date:
            db.add(PaymentRecord(
                subscription_id=sub.id,
                amount=sub.amount,
                currency=sub.currency,
                payment_date=old_date,
                status="pending",
            ))
            sub.next_payment_date = new_date
            updated += 1
    if updated:
        db.commit()
        logger.info(f"自动推进了 {updated} 个订阅的下次付款日期")


def _auto_disable_expired(db):
    from datetime import date
    today = date.today()
    count = (
        db.query(Subscription)
        .filter(
            Subscription.is_active == True,
            Subscription.expiry_date != None,
            Subscription.expiry_date < today,
        )
        .update({Subscription.is_active: False})
    )
    if count:
        db.commit()
        logger.info(f"已自动停用 {count} 个过期订阅")


async def _check_budget_alert(db):
    from datetime import date
    from app.services.notifier import notifier
    from app.services.billing import calculate_monthly_projection
    from app.services.exchange_rate import exchange_rate_service

    settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
    if not settings or not settings.monthly_budget or settings.monthly_budget <= 0:
        return

    preferred = settings.preferred_currency
    subscriptions = db.query(Subscription).filter(Subscription.is_active == True).all()

    spent = 0.0
    month_start = date.today().replace(day=1)
    for sub in subscriptions:
        proj = calculate_monthly_projection(sub, month_start)
        if proj is not None:
            converted = await exchange_rate_service.convert(db, proj, sub.currency, preferred)
            spent += converted

    spent = round(spent, 2)
    budget = settings.monthly_budget
    ratio = spent / budget

    if ratio < 0.8:
        return

    if ratio >= 1.0:
        message = f"本月支出已超出预算！已花费 {preferred} {spent:.2f}，预算 {preferred} {budget:.2f}"
    else:
        message = f"本月支出已达预算的 {int(ratio * 100)}%！已花费 {preferred} {spent:.2f}，预算 {preferred} {budget:.2f}"

    title = "SubLedger 预算告警"
    if settings.smtp_host:
        try:
            await notifier.send_email(subject=title, body=message, settings=settings)
        except Exception:
            logger.exception("预算告警邮件发送失败")
    if settings.bark_url:
        try:
            await notifier.send_bark(title=title, body=message, bark_url=settings.bark_url)
        except Exception:
            logger.exception("预算告警 Bark 推送失败")
    elif settings.serverchan_key:
        try:
            await notifier.send_serverchan(title=title, body=message, key=settings.serverchan_key)
        except Exception:
            logger.exception("预算告警 Server酱推送失败")
    elif settings.wechat_webhook_url:
        try:
            await notifier.send_wechat_webhook(title=title, body=message, webhook_url=settings.wechat_webhook_url)
        except Exception:
            logger.exception("预算告警企业微信推送失败")
    if settings.webhook_url:
        try:
            await notifier.send_webhook(title=title, body=message, subscription_id=0, webhook_url=settings.webhook_url)
        except Exception:
            logger.exception("预算告警 Webhook 发送失败")

    logger.info(f"已发送预算告警: {message}")




def start_scheduler():
    scheduler.add_job(
        daily_check_job,
        "cron",
        hour=0,
        minute=0,
        id="daily_subscription_check",
        replace_existing=True,
    )
    scheduler.add_job(
        backup_job,
        "cron",
        hour=3,
        minute=0,
        id="auto_backup",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("定时任务已启动")


def stop_scheduler():
    scheduler.shutdown()
    logger.info("定时任务已停止")