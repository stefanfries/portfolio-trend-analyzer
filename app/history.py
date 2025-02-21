import asyncio
import os
from datetime import datetime, timedelta
from typing import Optional

import httpx

from app.models.history import HistoryData, Interval
from app.settings import APISettings


def is_intraday(interval: Interval) -> bool:
    return interval in ["5min", "15min", "30min", "hour"]


async def is_api_up():
    api_settings = APISettings()

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(api_settings.api_url, timeout=5.0)
            if response.status_code == 200:
                return True
        except httpx.RequestError:
            pass
    return False


async def wake_up_api() -> bool:
    api_settings = APISettings()

    async with httpx.AsyncClient() as client:
        for _ in range(api_settings.api_wakeup_retries):
            try:
                print("🔄 Pinging API to wake it up...")
                response = await client.get(api_settings.api_url, timeout=5.0)
                if response.status_code == 200:
                    print("✅ API is awake!")
                    return True
            except httpx.RequestError:
                pass
            await asyncio.sleep(api_settings.api_wakeup_retries_delay_seconds)
    return False


async def get_history(
    instrument_id: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    interval: Optional[Interval] = None,
    id_notation: Optional[str] = None,
) -> HistoryData:

    if interval is None:
        interval = "day"

    if end is None or end > datetime.now():
        end = datetime.now()
    if start is None or start > end or is_intraday(interval):
        start = end - timedelta(days=14)
    end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)

    match id_notation:
        case "preferred_id_notation_exchange_trading":
            id_notation = "preferred_id_notation_exchange_trading"
        case "preferred_id_notation_life_trading":
            id_notation = "preferred_id_notation_life_trading"
        case [None, _]:
            id_notation = "default_id_notation"

    params = {
        "END": end.strftime("%d.%m.%Y"),
        "START": start.strftime("%d.%m.%Y"),
        "ID_NOTATION": id_notation,
        "INTERVALL": interval,
    }

    if not await is_api_up():
        await wake_up_api()

    async with httpx.AsyncClient() as client:
        try:
            url = f"{os.environ['API_URL']}/history/{instrument_id}"  # Morgan Stanley Call 19.12.25 NVIDIA
            print(f"Requesting {url}")
            response = await client.get(url, params=params)
            data = response.json()
            return HistoryData(**data)
        except httpx.RequestError as e:
            print(f"Error: {e}")
            return None
        except httpx.HTTPStatusError as e:
            print(f"Error: {e}")
            return None
