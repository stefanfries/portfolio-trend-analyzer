import asyncio
import sys
from datetime import datetime, timedelta

import pandas as pd

from app.analysis import detect_trend_break

# Fix Windows console encoding for emoji support
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from app.depots import (
    depot_900_prozent,  # noqa: F401
    etf_depot,  # noqa: F401
    mega_trend_folger,  # noqa: F401
    mtf_underlyings,  # noqa: F401
    my_mega_trend_folger,  # noqa: F401
    os_projekt_2025,  # noqa: F401
    test_depot,  # noqa: F401
    tsi_6i_aktien,  # noqa: F401
    tsi_6i_faktor2,  # noqa: F401
)
from app.notifier import send_mail  # noqa: F401
from app.reader import datareader
from app.results_saver import save_results_to_xlsx
from app.visualizer import plot_candlestick


async def main():
    # Configuration
    HISTORY_DAYS = 14
    TIMEFRAME = "hourly"  # Options: "hourly" or "daily"
    INSTRUMENT_TYPE = "warrant"  # Options: "stock" or "warrant"
    INTERVAL_MAP = {"hourly": "hour", "daily": "day"}

    # depot = test_depot
    # depot = tsi_6i_aktien
    # depot = tsi_6i_faktor2
    depot = mega_trend_folger
    depot_name = "mega_trend_folger"
    # depot = mtf_underlyings
    # depot_name = "mtf_underlyings"
    # depot = my_mega_trend_folger
    # depot = depot_900_prozent
    # depot = etf_depot
    # depot = os_projekt_2025

    results = []  # Collect all analysis results

    total_securities = len(depot)
    print(f"\n{'=' * 80}")
    print(f"🚀 Starting analysis of {total_securities} securities from depot")
    print(f"{'=' * 80}\n")

    for index, wkn in enumerate(depot, start=1):
        print(f"📊 [{index}/{total_securities}] Processing {wkn}...")
        result = await datareader(
            wkn,
            start=datetime.now() - timedelta(days=HISTORY_DAYS),
            id_notation="preferred_id_notation_life_trading",
            interval=INTERVAL_MAP[TIMEFRAME],
        )  # type: ignore

        if result is None:
            print(f"❌ Could not retrieve data for {wkn}")
            print(f"{'-' * 80}\n")
            continue

        metadata, df = result
        wkn = metadata.get("wkn")
        name = metadata.get("name")
        interval = metadata.get("interval")
        api_start = metadata.get("start")
        api_end = metadata.get("end")
        print(
            f"Analysing history of {wkn} ({name}), last {HISTORY_DAYS} days, interval: {interval}"
        )
        print(f"API returned data from {api_start} to {api_end} ({len(df)} data points)")

        # Detect trend breaks using multi-indicator analysis
        trend_signal = detect_trend_break(df, timeframe=TIMEFRAME, instrument_type=INSTRUMENT_TYPE)

        # Debug: Show data range for verification
        data_high = df["high"].max()
        data_low = df["low"].min()
        recent_high = trend_signal["metrics"]["recent_high"]
        current = trend_signal["metrics"]["current_price"]

        print(f"📍 Data: High={data_high:.2f}€, Low={data_low:.2f}€, Current={current:.2f}€")
        print(f"🎯 Used High={recent_high:.2f}€ for drawdown calculation")
        print(
            f"Trend Signal: {trend_signal['action']} (Drawdown: {trend_signal['metrics']['drawdown_pct']:.2f}%, ADX: {trend_signal['metrics']['adx']:.1f})"
        )

        plot_candlestick(df, wkn, name, timeframe=TIMEFRAME)  # type: ignore

        # Collect results for email report
        supertrend_direction = (
            "UP" if trend_signal["metrics"]["supertrend_direction"] == 1 else "DOWN"
        )
        results.append(
            {
                "WKN": wkn,
                "Name": name,
                "Supertrend": supertrend_direction,
                "Trend Signal": trend_signal["action"],
                "ADX": f"{trend_signal['metrics']['adx']:.1f}",
                "Drawdown %": f"{trend_signal['metrics']['drawdown_pct']:.2f}",
                "Current Price": f"{df['close'].iloc[-1]:.2f} €",
                "Reason": trend_signal["reason"],
            }
        )
        print(f"{'-' * 80}\n")

    print(f"{'=' * 80}")
    print(
        f"✅ Analysis complete! Processed {len(results)} out of {total_securities} securities successfully."
    )
    print(f"{'=' * 80}\n")

    # Save results for historical comparison (Excel format with proper formatting)
    if results:
        save_results_to_xlsx(results, depot_name=depot_name)

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
