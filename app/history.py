import httpx
import os
import asyncio
from app.settings import APISettings


async def wake_up_api():
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


async def get_history():

    await wake_up_api()
    
    async with httpx.AsyncClient() as client:
        try:
            url = f"{os.environ['API_URL']}/history/apple"
            print(f"Requesting {url}")
            response = await client.get(url)
            return response.json()
        except httpx.RequestError as e:
            print(f"Error: {e}")
            return None
        except httpx.HTTPStatusError as e:
            print(f"Error: {e}")
            return None
        except httpx.TimeoutException as e:
            print(f"Error: {e}")
            return None
        