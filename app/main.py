import asyncio
from datetime import datetime, timedelta

import pandas as pd

from app.analysis import fit_parabola, generate_recommendation
from app.depots import (
    depot_900_prozent,
    etf_depot,
    mega_trend_folger,
    my_mega_trend_folger,
    test_depot,
    tsi_6i_aktien,
    tsi_6i_faktor2,
)
from app.notifier import send_mail
from app.reader import datareader
from app.visualizer import plot_candlestick


async def main():
    # depot = test_depot
    # depot = tsi_6i_aktien
    # depot = tsi_6i_faktor2
    depot = my_mega_trend_folger
    # depot = depot_900_prozent
    # depot = etf_depot
    history_days = 14
    for wkn in depot:
        df = pd.DataFrame()
        metadata, df = await datareader(
            wkn,
            start=datetime.now() - timedelta(days=history_days),
            id_notation="preferred_id_notation_life_trading",
            interval="day",
        )  # type: ignore

        if df is None:
            print(f"Could not retrieve data for {wkn}")
            continue
        # plot_candlestick(df, title=wkn)
        parabola_parms = fit_parabola(df)
        print(f"Analysing history of {wkn}, last {history_days} days")
        recommendation = generate_recommendation(parabola_parms)
        print(f"Recommendation: {recommendation}")
        print()

    to_email = "stefan.fries.burgdorf@gmx.de"
    subject = "Securities Analysis and Recommendations"
    message = """
    <html>
    <head>
        <style>
            table {{ border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; }}
            th, td {{ border: 1px solid black; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <p>Hello Stefan,</p>
        <p>here is the securities history you requested:</p>
        {table}
        <p>Best regards,<br>Your Securities Bot</p>
    </body>
    </html>
    """

    if df is not None:
        table_html = df.to_html(index=False, border=1)
        message = message.format(table=table_html)

    # send_mail(subject, message, to_email)


if __name__ == "__main__":
    asyncio.run(main())
