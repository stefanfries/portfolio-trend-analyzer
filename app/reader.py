import asyncio
from datetime import datetime, timedelta
from typing import Optional

import httpx
import pandas as pd

from app.models import Interval
from app.settings import APISettings


def is_intraday(interval: Interval) -> bool:
    return interval in ["5min", "15min", "30min", "hour"]


async def is_api_up():

    api_settings = APISettings()

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                api_settings.api_url, timeout=api_settings.api_timeout
            )
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
                response = await client.get(
                    api_settings.api_url, timeout=api_settings.api_timeout
                )
                if response.status_code == 200:
                    print("✅ API is awake!")
                    return True
                else:
                    print(
                        f"❌ API is down! Retrying in {api_settings.api_timeout} seconds..."
                    )
            except httpx.RequestError:
                pass
            await asyncio.sleep(api_settings.api_wakeup_retries_delay_seconds)
    return False


async def datareader(
    instrument_id: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    interval: Interval = "day",
    id_notation: str = "default_id_notation",
) -> Optional[pd.DataFrame]:

    now = datetime.now()

    # Adjust end date to now if not provided or in the future
    end = min(end or now, now)
    end = end.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Adjust start date to 14 days before end date if not provided or in the future
    if start is None or start > end or is_intraday(interval):
        start = end - timedelta(days=28)
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)

    # Normalize id_notation values
    if id_notation not in [
        "preferred_id_notation_exchange_trading",
        "preferred_id_notation_life_trading",
    ]:
        id_notation = "default_id_notation"

    # API query parameters
    params = {
        "start": start.strftime("%Y-%m-%d"),
        "end": end.strftime("%Y-%m-%d"),
        "id_notation": id_notation,
        "interval": interval,
    }

    # Ensure API is up and running
    if not await is_api_up():
        await wake_up_api()

    api_settings = APISettings()
    url = f"{api_settings.api_url}/history/{instrument_id}"

    async with httpx.AsyncClient() as client:
        try:
            print("⚡ Fetching data from API...")
            response = await client.get(url, params=params)
            response.raise_for_status()

            history_data = response.json().get("data", [])
            if not history_data:
                print("⚠️ Warning: No data returned from API")
                return None

            df = pd.DataFrame(history_data)
            df["datetime"] = pd.to_datetime(df["datetime"])
            return df

        except httpx.HTTPStatusError as e:
            print(f"❌ Error: {e}")
            return None

        except httpx.RequestError as e:
            print(f"❌ Error: {e}")
            return None
