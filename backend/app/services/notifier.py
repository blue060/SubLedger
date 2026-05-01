import logging
from datetime import date, timedelta

import aiosmtplib
from email.mime.text import MIMEText

import httpx
from sqlalchemy.orm import Session

from app.models import AppSettings, Notification, Subscription

logger = logging.getLogger("subledger")


class Notifier:
    async def send(self, notification: Notification, settings: AppSettings, db: Session) -> None:
        if settings.smtp_host:
            try:
                await self.send_email(
                    subject="SubLedger 订阅提醒",
                    body=notification.message,
                    settings=settings,
                )
                notification.sent_email = True
            except Exception:
                pass

        if settings.bark_url:
            try:
                await self.send_bark(
                    title="SubLedger 订阅提醒",
                    body=notification.message,
                    bark_url=settings.bark_url,
                )
                notification.sent_push = True
            except Exception:
                pass

        elif settings.serverchan_key:
            try:
                await self.send_serverchan(
                    title="SubLedger 订阅提醒",
                    body=notification.message,
                    key=settings.serverchan_key,
                )
                notification.sent_push = True
            except Exception:
                pass

        db.commit()

    async def send_email(self, subject: str, body: str, settings: AppSettings) -> None:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = settings.smtp_from or settings.smtp_user
        msg["To"] = settings.smtp_user

        if settings.smtp_tls:
            await aiosmtplib.send(
                msg,
                hostname=settings.smtp_host,
                port=settings.smtp_port or 465,
                username=settings.smtp_user,
                password=settings.smtp_password,
                use_tls=True,
            )
        else:
            await aiosmtplib.send(
                msg,
                hostname=settings.smtp_host,
                port=settings.smtp_port or 587,
                username=settings.smtp_user,
                password=settings.smtp_password,
                start_tls=True,
            )

    async def send_bark(self, title: str, body: str, bark_url: str) -> None:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.get(f"{bark_url.rstrip('/')}/{title}/{body}")

    async def send_serverchan(self, title: str, body: str, key: str) -> None:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                f"https://sctapi.ftqq.com/{key}.send",
                data={"title": title, "desp": body},
            )


notifier = Notifier()


async def check_upcoming_subscriptions(db: Session) -> None:
    settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
    if not settings:
        return

    reminder_days = settings.reminder_days
    today = date.today()
    end_date = today + timedelta(days=reminder_days)

    subs = (
        db.query(Subscription)
        .filter(
            Subscription.is_active == True,
            Subscription.notify == True,
            Subscription.next_payment_date >= today,
            Subscription.next_payment_date <= end_date,
        )
        .all()
    )

    for sub in subs:
        existing = (
            db.query(Notification)
            .filter(
                Notification.subscription_id == sub.id,
                Notification.notify_date == sub.next_payment_date,
            )
            .first()
        )
        if existing:
            continue

        currency_symbols = {"CNY": "¥", "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "HKD": "$"}
        symbol = currency_symbols.get(sub.currency, sub.currency)
        message = f"{sub.name} 将于 {sub.next_payment_date} 扣款 {symbol}{sub.amount:.2f}"

        notification = Notification(
            subscription_id=sub.id,
            message=message,
            notify_date=sub.next_payment_date,
        )
        db.add(notification)
        db.flush()

        await notifier.send(notification, settings, db)