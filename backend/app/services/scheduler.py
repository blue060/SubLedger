import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.database import SessionLocal
from app.models import Subscription, AppSettings, User
from app.services.notifier import check_upcoming_subscriptions
from app.services.payment_sync import sync_due_payments
from app.services.backup import perform_backup
from app.services.subscription_lifecycle import deactivate_expired_subscriptions

logger = logging.getLogger("subledger")

scheduler = AsyncIOScheduler()


async def daily_check_job():
    logger.info("开始检查即将到期的订阅...")
    db = SessionLocal()
    try:
        await check_upcoming_subscriptions(db)
        _advance_overdue_payment_dates(db)
        count = deactivate_expired_subscriptions(db)
        if count:
            logger.info(f"已自动停用 {count} 个过期订阅")
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
        admin = db.query(User).filter(User.is_admin == True).order_by(User.id).first()
        if not admin:
            logger.warning("自动备份已跳过：没有管理员账户")
            return
        perform_backup(db, admin.id)
    except Exception as e:
        logger.error(f"自动备份失败: {e}")
    finally:
        db.close()


def _advance_overdue_payment_dates(db):
    sync_due_payments(db)


async def _check_budget_alert(db):
    from datetime import date
    from app.services.notifier import notifier
    from app.services.billing import calculate_monthly_projection
    from app.services.exchange_rate import exchange_rate_service

    settings_rows = db.query(AppSettings).filter(AppSettings.monthly_budget > 0).all()
    month_start = date.today().replace(day=1)

    for settings in settings_rows:
        preferred = settings.preferred_currency
        subscriptions = db.query(Subscription).filter(
            Subscription.user_id == settings.user_id,
            Subscription.is_active == True,
        ).all()

        spent = 0.0
        for sub in subscriptions:
            proj = calculate_monthly_projection(sub, month_start)
            if proj is not None:
                spent += await exchange_rate_service.convert(db, proj, sub.currency, preferred)

        spent = round(spent, 2)
        budget = settings.monthly_budget
        ratio = spent / budget
        if ratio < 0.8:
            continue

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

        logger.info("已发送用户 %s 的预算告警: %s", settings.user_id, message)




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
