import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.database import SessionLocal
from app.services.notifier import check_upcoming_subscriptions

logger = logging.getLogger("subledger")

scheduler = AsyncIOScheduler()


async def daily_check_job():
    logger.info("开始检查即将到期的订阅...")
    db = SessionLocal()
    try:
        await check_upcoming_subscriptions(db)
    except Exception as e:
        logger.error(f"订阅检查任务失败: {e}")
    finally:
        db.close()
    logger.info("订阅检查完成")


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