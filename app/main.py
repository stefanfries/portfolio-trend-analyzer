import asyncio

import pandas as pd
from dotenv import find_dotenv, load_dotenv

from app.history import get_history
from app.mail import send_mail


async def main():
    print(find_dotenv())
    load_dotenv(find_dotenv())

    depot = [
        "JK2M14",
        # "MB76DR",
        # "JK3KVQ", check error in /basedata endpoint
        # "ME2CU8",
        # "MJ1278",
        # "JK6CRM",
        # "JV8872",
        # "MG80MS",
        # "HS75W5",
        # "HT2081",
        # "HS2RHM",
    ]

    for instrument_id in depot:
        history = await get_history(instrument_id)
        history_data = history.data
        df = pd.DataFrame([record.model_dump() for record in history_data])
        # stock_history = stock_history.model_dump_json()
        print(df)
        # df = pd.DataFrame(stock_history["data"])
        # df.head()
        # print(stock_history.model_dump_json(indent=4))
        # if stock_history:
        # print(stock_history.model_dump_json(indent=4))
        # df = pd.DataFrame(json.loads(stock_history["data"]))
        # df.head()

    # subject = "Test Email"
    # to_email = "stefan.fries.burgdorf@gmx.de"
    # message = f"Hello Stefan,\n\nHere is the securities history you requested:\n\n"
    # message = message + stock_history.model_dump_json(indent=4)
    # print(message)
    # send_mail(subject, message, to_email)


if __name__ == "__main__":
    asyncio.run(main())
