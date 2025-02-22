import asyncio

from app.depots import mega_trend_folger as depot
from app.notifier import send_mail
from app.reader import datareader


async def main():

    for wkn in depot:
        df = await datareader(wkn)

    subject = "Test Email"
    to_email = "stefan.fries.burgdorf@gmx.de"
    message = f"Hello Stefan,\n\nHere is the securities history you requested:\n\n"

    if df is not None:
        message = message + str(df)
    print(message)
    send_mail(subject, message, to_email)


if __name__ == "__main__":
    asyncio.run(main())
