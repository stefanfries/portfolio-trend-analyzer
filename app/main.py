from app.mail import send_mail
from app.history import get_history
from dotenv import find_dotenv, load_dotenv
import os
import asyncio
import json


async def main():
    print(find_dotenv())
    load_dotenv(find_dotenv())

    stock_history = await get_history()
    stock_history = stock_history["data"][0]
    subject = "Test Email"
    message = "This is a test email sent from Python."
    to_email = "stefan.fries.burgdorf@gmx.de"
    message = f"Hello Stefan,\n\nHere is the stock history you requested:"
    message = message + "\n\n" + json.dumps(stock_history, indent=4)
    print(message)
    send_mail(subject, message, to_email)


if __name__ == "__main__":
    asyncio.run(main())
