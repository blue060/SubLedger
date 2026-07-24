import json
import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.config import get_settings
from app.exceptions import ExchangeRateError
from app.models import AppSettings

logger = logging.getLogger("subledger")

BASE_URL = "https://open.er-api.com/v6/latest/USD"


class ExchangeRateService:
    def __init__(self):
        self._memory_rates: dict[str, float] | None = None
        self._memory_expires_at: datetime | None = None
        self._refresh_lock = asyncio.Lock()

    async def get_rates(self, db: Session) -> dict[str, float]:
        now = datetime.now(timezone.utc)
        if self._memory_rates and self._memory_expires_at and now < self._memory_expires_at:
            return self._memory_rates

        async with self._refresh_lock:
            now = datetime.now(timezone.utc)
            if self._memory_rates and self._memory_expires_at and now < self._memory_expires_at:
                return self._memory_rates

            settings_row = db.query(AppSettings).filter(AppSettings.id == 1).first()
            if not settings_row:
                settings_row = AppSettings(id=1, preferred_currency="CNY", reminder_days=7)
                db.add(settings_row)
                db.commit()
                db.refresh(settings_row)

            cache_hours = get_settings().EXCHANGE_RATE_CACHE_HOURS
            expires_at = now + timedelta(hours=cache_hours)
            if (
                settings_row.exchange_rate_cache
                and settings_row.exchange_rate_updated_at
                and (now - settings_row.exchange_rate_updated_at.replace(tzinfo=timezone.utc)) < timedelta(hours=cache_hours)
            ):
                self._memory_rates = json.loads(settings_row.exchange_rate_cache)
                self._memory_expires_at = expires_at
                return self._memory_rates

            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    resp = await client.get(BASE_URL)
                    resp.raise_for_status()
                    data = resp.json()
            except Exception as e:
                logger.warning(f"汇率 API 请求失败: {e}")
                if settings_row.exchange_rate_cache:
                    self._memory_rates = json.loads(settings_row.exchange_rate_cache)
                    self._memory_expires_at = now + timedelta(minutes=15)
                    return self._memory_rates
                raise ExchangeRateError("汇率服务暂时不可用，且无缓存数据")

            rates = data.get("rates", {})
            settings_row.exchange_rate_cache = json.dumps(rates)
            settings_row.exchange_rate_updated_at = now
            db.commit()
            self._memory_rates = rates
            self._memory_expires_at = expires_at
            return rates

    async def convert(
        self, db: Session, amount: float, from_currency: str, to_currency: str
    ) -> float:
        if from_currency == to_currency:
            return amount

        rates = await self.get_rates(db)

        from_rate = rates.get(from_currency)
        to_rate = rates.get(to_currency)
        if from_rate is None or to_rate is None:
            raise ExchangeRateError(f"不支持的货币: {from_currency} 或 {to_currency}")

        return amount * (to_rate / from_rate)


exchange_rate_service = ExchangeRateService()
