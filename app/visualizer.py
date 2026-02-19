from datetime import date
from pathlib import Path

import matplotlib
import mplfinance as mpf
import numpy as np
import pandas as pd
import talib

from app.indicators import supertrend
from app.trend_config import get_config

matplotlib.use("Agg")  # Use non-interactive backend - saves files without showing GUI


def plot_candlestick(df: pd.DataFrame, wkn: str, name: str, timeframe: str = "hourly") -> None:
    """Plot a candlestick chart with technical indicators.

    Creates a 2-panel chart:
    - Panel 0: Candlesticks + Supertrend + EMAs
    - Panel 1: ADX + Plus DI + Minus DI

    Args:
        df: DataFrame with OHLC data
        wkn: Security identifier
        name: Security name
        timeframe: 'hourly' or 'daily' for indicator configuration
    """

    # Ensure charts directory exists
    charts_dir = Path("charts")
    charts_dir.mkdir(exist_ok=True)

    # Get configuration for indicator parameters
    config = get_config(timeframe)

    # Prepare data
    df_plot = df.copy()
    df_plot = df_plot.set_index("datetime")
    df_plot = df_plot.sort_index(ascending=True)

    # Extract arrays for indicator calculation
    high = df_plot["high"].to_numpy()
    low = df_plot["low"].to_numpy()
    close = df_plot["close"].to_numpy()

    # ========== Panel 0: Price Chart with Supertrend and EMAs ==========

    # Calculate Supertrend
    st_values, st_direction = supertrend(
        df_plot["high"],
        df_plot["low"],
        df_plot["close"],
        atr_period=config["supertrend_atr_period"],
        multiplier=config["supertrend_multiplier"],
    )

    # Separate uptrend and downtrend for different colors
    supertrend_up = np.where(st_direction > 0, st_values, np.nan)
    supertrend_down = np.where(st_direction < 0, st_values, np.nan)

    # Calculate EMAs
    ema_fast = talib.EMA(close, timeperiod=config["ema_fast_period"])
    ema_slow = talib.EMA(close, timeperiod=config["ema_slow_period"])

    # ========== Panel 1: ADX and Directional Indicators ==========

    adx = talib.ADX(high, low, close, timeperiod=config["adx_period"])
    plus_di = talib.PLUS_DI(high, low, close, timeperiod=config["adx_period"])
    minus_di = talib.MINUS_DI(high, low, close, timeperiod=config["adx_period"])

    # Create threshold line for ADX at 25
    adx_threshold = np.full(len(df_plot), config["min_adx_strength"])

    # ========== Create Additional Plots ==========

    apds = [
        # Panel 0: Price chart overlays
        mpf.make_addplot(
            supertrend_up,
            panel=0,
            color="green",
            width=1.5,
            secondary_y=False,
            label="Supertrend Up",
        ),
        mpf.make_addplot(
            supertrend_down,
            panel=0,
            color="red",
            width=1.5,
            secondary_y=False,
            label="Supertrend Down",
        ),
        mpf.make_addplot(
            ema_fast,
            panel=0,
            color="blue",
            width=1,
            secondary_y=False,
            label=f"EMA{config['ema_fast_period']}",
        ),
        mpf.make_addplot(
            ema_slow,
            panel=0,
            color="orange",
            width=1,
            secondary_y=False,
            label=f"EMA{config['ema_slow_period']}",
        ),
        # Panel 1: ADX and directional indicators
        mpf.make_addplot(adx, panel=1, color="purple", width=1.5, secondary_y=False, ylabel="ADX"),
        mpf.make_addplot(
            plus_di, panel=1, color="green", width=1, secondary_y=False, label="+DI (bullish)"
        ),
        mpf.make_addplot(
            minus_di, panel=1, color="red", width=1, secondary_y=False, label="-DI (bearish)"
        ),
        mpf.make_addplot(
            adx_threshold,
            panel=1,
            color="gray",
            width=0.8,
            linestyle="dashed",
            secondary_y=False,
            label="ADX=25",
        ),
    ]

    # Remove None values
    apds = [ap for ap in apds if ap is not None]

    # ========== Create the Chart ==========

    chart_filename = f"candlestick_{wkn}_{date.today():%Y-%m-%d}.png"
    chart_path = charts_dir / chart_filename

    # Create custom style with larger figure
    custom_style = mpf.make_mpf_style(base_mpf_style="charles")

    # Calculate y-axis limits for price panel (min to max with padding)
    max_price = max(df_plot["high"].max(), ema_fast.max(), ema_slow.max(), np.nanmax(st_values))
    min_price = min(
        df_plot["low"].min(), np.nanmin(ema_fast), np.nanmin(ema_slow), np.nanmin(st_values)
    )

    # Add 5% padding on both sides
    price_range = max_price - min_price
    ylim_main = (min_price - price_range * 0.05, max_price + price_range * 0.05)

    fig, axes = mpf.plot(
        data=df_plot,
        type="candle",
        style=custom_style,
        title=f"{name} ({wkn}) - Multi-Indicator Analysis",
        ylabel="Price (€)",
        addplot=apds,
        panel_ratios=(3, 1),  # Price panel larger, ADX panel smaller
        figsize=(14, 8),  # 2-panel layout
        ylim=ylim_main,
        returnfig=True,
    )

    # Add separator line between panels
    # axes[0] is main price panel, axes[2] is ADX panel
    if len(axes) > 2:
        # Add thick line on top and bottom of price panel
        axes[0].spines["top"].set_linewidth(1)
        axes[0].spines["top"].set_color("black")
        axes[0].spines["bottom"].set_linewidth(1)
        axes[0].spines["bottom"].set_color("black")
        # Add thick line on top and bottom of ADX panel
        axes[2].spines["top"].set_linewidth(1)
        axes[2].spines["top"].set_color("black")
        axes[2].spines["bottom"].set_linewidth(1)
        axes[2].spines["bottom"].set_color("black")

    # Save the figure
    fig.savefig(str(chart_path), dpi=100, bbox_inches="tight")

    print(f"📊 Chart saved as {chart_path}")
