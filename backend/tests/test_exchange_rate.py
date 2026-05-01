import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest


def test_exchange_rate_convert_same_currency():
    from app.services.exchange_rate import ExchangeRateService
    import asyncio

    service = ExchangeRateService()

    async def run():
        return await service.convert(None, 100.0, "CNY", "CNY")

    result = asyncio.run(run())
    assert result == 100.0