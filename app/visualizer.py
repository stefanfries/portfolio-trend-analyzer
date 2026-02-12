from datetime import date
from pathlib import Path

import matplotlib
import mplfinance as mpf
import numpy as np
import pandas as pd

# import pandas_ta as ta

# from app.indicators import pandas_supertrend

matplotlib.use("Agg")  # Use non-interactive backend - saves files without showing GUI


def plot_candlestick(df: pd.DataFrame, wkn: str, name: str) -> None:
    """Plot a candlestick chart for the given security data."""

    # Ensure charts directory exists
    charts_dir = Path("charts")
    charts_dir.mkdir(exist_ok=True)

    df = df.set_index("datetime")  # Make the datetime column an index
    if "volume" in df.columns and df["volume"].nunique() == 1:
        df["volume"] += 1  # Avoids singular transformation error

    df = df.sort_index(ascending=True)

    # Compute RSI (14-period) using TA-Lib
    # df["RSI"] = talib.RSI(df["close"], timeperiod=14)

    # Create RSI subplot
    # rsi_plot = mpf.make_addplot(df["RSI"], panel=1, color="blue", secondary_y=False)

    # Calculate Bollinger Bands using TA-Lib
    # df["BBU"], _, df["BBL"] = talib.BBANDS(
    #     df["close"], timeperiod=20, nbdevup=2, nbdevdn=2
    # )

    """
    # Calculate Donchian Channels (20-period high/low)
    df["DCL"] = df["low"].rolling(20).min()  # Lower boundary
    df["DCU"] = df["high"].rolling(20).max()  # Upper boundary

    # Linear Regression Trendlines (Last 20 periods)
    n = 20  # Number of periods to consider for trendlines
    recent_df = df[-n:]  # Select last 'n' periods

    # Fit regression for Support & Resistance
    x = np.arange(n)
    slope_low, intercept_low, _, _, _ = linregress(x, recent_df["low"])
    slope_high, intercept_high, _, _, _ = linregress(x, recent_df["high"])

    # Compute trendlines only for the last 'n' periods
    trendline_x = np.arange(n)  # Use only the range of the last 'n' periods
    support_trendline = slope_low * trendline_x + intercept_low
    resistance_trendline = slope_high * trendline_x + intercept_high

    # Create arrays for trendlines with same length as original dataframe
    trendline_support_full = np.full(len(df), np.nan)
    trendline_resistance_full = np.full(len(df), np.nan)

    # Place the computed trendlines only on the last 'n' periods
    trendline_support_full[-n:] = support_trendline
    trendline_resistance_full[-n:] = resistance_trendline

    ## Compute trendlines for full data
    # df["Support_Trendline"] = slope_low * np.arange(len(df)) + intercept_low
    # df["Resistance_Trendline"] = slope_high * np.arange(len(df)) + intercept_high

    """
    # Compute Supertrend indicator
    # df["supertrend"], df["direction"] = supertrend(df["high"], df["low"], df["close"])
    # df.ta.supertrend(atr_period=7, multiplier=3, append=True)

    # Separate Uptrend & Downtrend values for plotting
    # supertrend_up = np.where(df["direction"] > 0, df["supertrend"], np.nan)
    # supertrend_down = np.where(df["direction"] < 0, df["supertrend"], np.nan)
    # supertrend_up = np.where(df["SUPERTd_7_3.0"] > 0, df["SUPERTs_7_3.0"], np.nan)
    # supertrend_down = np.where(df["SUPERTd_7_3.0"] < 0, df["SUPERTl_7_3.0"], np.nan)

    # Create plots for the Supertrend indicator
    # ap_up = (
    #     mpf.make_addplot(supertrend_up, panel=0, color="green", secondary_y=False)
    #     if not np.all(np.isnan(supertrend_up))
    #     else None
    # )
    # ap_down = (
    #     mpf.make_addplot(supertrend_down, panel=0, color="red", secondary_y=False)
    #     if not np.all(np.isnan(supertrend_down))
    #     else None
    # )

    # Convert datetime index to numerical values using mdates.date2num

    df["index_number"] = np.arange(len(df))
    # Quadratic regression (parabola fit)
    coeffs = np.polyfit(df["index_number"], df["close"], 2)
    a, b, c = coeffs  # Coefficients of the parabola

    # def parabola function
    def parabola(x):
        return a * x**2 + b * x + c

    df["parabola"] = df["index_number"].map(parabola)

    # Plotting with mplfinance
    apds = [
        # mpf.make_addplot(
        #     df["BBL"], color="blue", linestyle="dotted"
        # ),  # Bollinger Lower Band
        # mpf.make_addplot(
        #     df["BBU"], color="blue", linestyle="dotted"
        # ),  # Bollinger Upper Band
        # mpf.make_addplot(
        #     df["DCL"], color="purple", linestyle="dashed"
        # ),  # Donchian Lower
        # mpf.make_addplot(
        #     df["DCU"], color="purple", linestyle="dashed"
        # ),  # Donchian Upper
        # mpf.make_addplot(trendline_support_full, color="green"),  # Support Trendline
        # mpf.make_addplot(
        #     trendline_resistance_full, color="red"
        # ),  # Resistance Trendline
        #     ap_up,
        #     ap_down,
        # mpf.make_addplot(df["RSI"], panel=1, color="blue", secondary_y=False),
        mpf.make_addplot(df["parabola"], color="red", linestyle="dashed"),
    ]
    apds = [ap for ap in apds if ap is not None]  # Remove None values

    # Define figure with two panels (candlestick + RSI)
    chart_filename = f"candlestick_{wkn}_{date.today():%Y-%m-%d}.png"
    chart_path = charts_dir / chart_filename

    mpf.plot(
        data=df,
        # mav=(5, 10),
        type="candle",
        # show_nontrading=True,
        # volume=True,
        style="charles",
        title=f"Analysis for {name}",
        savefig=str(chart_path),
        returnfig=True,  # Get the fiure and axis to modify and save it later
        # addplot=rsi_plot,
        # panel_ratios=(3, 1),  # Larger main panel, smaller RSI panel
        ylabel="Price (€)",
        addplot=apds,
        # ylabel_lower="RSI",
    )

    print(f"📊 Chart saved as {chart_path}. Open it manually to view.")
