import asyncio
import tkinter
from datetime import datetime, timedelta

import pandas as pd

from app.analysis import fit_parabola, generate_recommendation
from app.depots import (
    depot_900_prozent,  # noqa: F401
    etf_depot,  # noqa: F401
    mega_trend_folger,  # noqa: F401
    my_mega_trend_folger,  # noqa: F401
    os_projekt_2025,  # noqa: F401
    test_depot,  # noqa: F401
    tsi_6i_aktien,  # noqa: F401
    tsi_6i_faktor2,  # noqa: F401
)
from app.notifier import send_mail  # noqa: F401
from app.reader import datareader
from app.visualizer import plot_candlestick

print(tkinter.TkVersion)  # Should print a version number


async def main():
    # depot = test_depot
    # depot = tsi_6i_aktien
    # depot = tsi_6i_faktor2
    depot = mega_trend_folger
    # depot = my_mega_trend_folger
    # depot = depot_900_prozent
    # depot = etf_depot
    # depot = os_projekt_2025

    history_days = 14
    results = []  # Collect all analysis results

    for wkn in depot:
        result = await datareader(
            wkn,
            start=datetime.now() - timedelta(days=history_days),
            id_notation="preferred_id_notation_life_trading",
            interval="hour",
        )  # type: ignore

        if result is None:
            print(f"❌ Could not retrieve data for {wkn}")
            continue

        metadata, df = result
        wkn = metadata.get("wkn")
        name = metadata.get("name")
        interval = metadata.get("interval")
        api_start = metadata.get("start")
        api_end = metadata.get("end")
        print(
            f"Analysing history of {wkn} ({name}), last {history_days} days, interval: {interval}"
        )
        print(f"API returned data from {api_start} to {api_end} ({len(df)} data points)")
        parabola_parms = fit_parabola(df)
        recommendation = generate_recommendation(parabola_parms)
        print(f"Recommendation: {recommendation}")
        plot_candlestick(df, wkn, name)  # type: ignore

        # Collect results for email report
        results.append(
            {
                "WKN": wkn,
                "Name": name,
                "Recommendation": recommendation,
                "Current Price": f"{df['close'].iloc[-1]:.2f} €",
            }
        )
        print()

    to_email = "stefan.fries.burgdorf@gmx.de"  # noqa: F841
    subject = "Securities Analysis and Recommendations"  # noqa: F841
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
        <p>here is the securities analysis and recommendations you requested:</p>
        {table}
        <p>Best regards,<br>Your Securities Bot</p>
    </body>
    </html>
    """

    if results:
        summary_df = pd.DataFrame(results)
        table_html = summary_df.to_html(index=False, border=1)
        message = message.format(table=table_html)
        # Uncomment to send email:
        # send_mail(subject, message, to_email)
    else:
        print("⚠️ No data was successfully retrieved for any security.")


if __name__ == "__main__":
    asyncio.run(main())
