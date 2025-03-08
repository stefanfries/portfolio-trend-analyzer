import asyncio
from datetime import datetime
from typing import Dict, Optional, Tuple

import httpx
import pandas as pd

from app.models import Interval
from app.settings import APISettings


def is_intraday(interval: Interval) -> bool:
    """
    Determines if the given interval is an intraday interval.
    Args:
        interval (Interval): The time interval to check.
    Returns:
        bool: True if the interval is an intraday interval (e.g., "5min", "15min", "30min", "hour"), False otherwise.
    """

    return interval in ["5min", "15min", "30min", "hour"]


async def is_api_up() -> bool:
    """
    Check if the API is up and running.
    This function sends a GET request to the API URL specified in the API settings.
    If the API responds with a status code of 200, it is considered up.
    Returns:
        bool: True if the API is up (status code 200), False otherwise.
    """

    api_settings = APISettings()  # type: ignore

    async with httpx.AsyncClient() as client:
        try:
            print("🔄 Checking whether API is up...")
            response = await client.get(
                api_settings.api_url, timeout=api_settings.api_timeout
            )
            if response.status_code == 200:
                return True
        except httpx.RequestError:
            pass
    return False


async def wake_up_api() -> bool:
    """
    Attempts to wake up an API by sending repeated GET requests until a successful response is received or the retry limit is reached.
    Returns:
        bool: True if the API responds with a status code of 200, indicating it is awake. False if the retry limit is reached without a successful response.
    Raises:
        httpx.RequestError: If there is an issue with the request, it will be caught and retried.
    """

    api_settings = APISettings()  # type: ignore

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
) -> Optional[Tuple[Dict[str, str], pd.DataFrame]]:
    """
    Fetch historical data for a given financial instrument from the API.
    Args:
        instrument_id (str): The ID of the financial instrument.
        start (Optional[datetime], optional): The start date for the data retrieval. Defaults to None.
        end (Optional[datetime], optional): The end date for the data retrieval. Defaults to None.
        interval (Interval, optional): The interval for the data (e.g., "day", "week"). Defaults to "day".
        id_notation (str, optional): The notation ID for the instrument. Defaults to "default_id_notation".
    Returns:
        Optional[Tuple[Dict[str, str], pd.DataFrame]]: A tuple containing metadata and a DataFrame with historical data, or None if an error occurs or no data is returned.
    """
    if id_notation not in [
        "preferred_id_notation_exchange_trading",
        "preferred_id_notation_life_trading",
    ]:
        id_notation = "default_id_notation"

    params = {
        "id_notation": id_notation,
        "interval": interval,
    }
    if start:
        params["start"] = start.strftime("%Y-%m-%dT%H:%M:%S")
    if end:
        params["end"] = end.strftime("%Y-%m-%dT%H:%M:%S")

    # Ensure API is up and running
    if not await is_api_up():
        await wake_up_api()

    api_settings = APISettings()  # type: ignore
    url = f"{api_settings.api_url}/{api_settings.api_history_path}/{instrument_id}"
    async with httpx.AsyncClient() as client:
        try:
            print("⚡ Fetching data from API...")
            response = await client.get(url, params=params)
            response.raise_for_status()

            json_response = response.json()

            metadata = {
                "wkn": json_response.get("wkn", []),
                "name": json_response.get("name", []),
                "id_notation": json_response.get("id_notation", []),
                "trading_venue": json_response.get("trading_venue", []),
                "currency": json_response.get("currency", []),
                "start": json_response.get("start", []),
                "end": json_response.get("end", []),
                "interval": json_response.get("interval", []),
            }

            history_data = json_response.get("data", [])
            if not history_data:
                print("⚠️ Warning: No data returned from API")
                return None

            df = pd.DataFrame(history_data)
            df["datetime"] = pd.to_datetime(df["datetime"])
            print(f"📈 Data for {metadata.get("name")} retrieved successfully!")
            return metadata, df

        except httpx.HTTPStatusError as e:
            print(f"❌ Error: {e}")
            return None

        except httpx.RequestError as e:
            print(f"❌ Error: {e}")
            return None
