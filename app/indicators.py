import numpy as np
import pandas as pd
import pandas_ta as ta
import talib


def pandas_supertrend(
    high, low, close, atr_period=7, multiplier=3.0
) -> tuple[pd.Series, pd.Series]:

    # Compute ATR using Pandas TA
    atr = ta.atr(high, low, close, length=atr_period)

    # Calculate basic upper and lower bands
    hl2 = (high + low) / 2
    upper_band = hl2 + (multiplier * atr)
    lower_band = hl2 - (multiplier * atr)

    # Initialize Supertrend and Trend Direction columns
    supertrend_values = pd.Series(index=close.index, dtype=float)
    trend_direction = pd.Series(index=close.index, dtype=float)

    # Compute Supertrend values and Trend direction
    for i in range(1, len(close)):
        # Set trend direction based on the previous day's close
        if close[i] > upper_band[i - 1]:
            trend_direction[i] = 1  # Uptrend
        elif close[i] < lower_band[i - 1]:
            trend_direction[i] = -1  # Downtrend
        else:
            trend_direction[i] = trend_direction[i - 1]  # Keep previous trend

        # Set Supertrend value based on trend direction
        if trend_direction[i] > 0:
            supertrend_values[i] = (
                max(lower_band[i], supertrend_values[i - 1])
                if supertrend_values[i - 1]
                else lower_band[i]
            )
        else:
            supertrend_values[i] = (
                min(upper_band[i], supertrend_values[i - 1])
                if supertrend_values[i - 1]
                else upper_band[i]
            )

    return supertrend_values, trend_direction


def supertrend(
    high, low, close, atr_period=7, multiplier=3.0
) -> tuple[np.ndarray, np.ndarray]:
    """
    Compute the Supertrend indicator using TA-Lib.

    Parameters:
    - df (pd.DataFrame): DataFrame with 'High', 'Low', and 'Close' columns
    - atr_period (int): ATR period (default 14)
    - multiplier (float): ATR multiplier (default 3)

    Returns:
    - df (pd.DataFrame): Original DataFrame with added 'Supertrend' and 'Trend' columns
    """

    # Convert Pandas Series to NumPy arrays to avoid Series indexing warnings
    close = close.to_numpy()
    high = high.to_numpy()
    low = low.to_numpy()

    # Compute ATR using TA-Lib
    atr = talib.ATR(high, low, close, timeperiod=atr_period)

    # Calculate basic upper and lower bands
    hl2 = (high + low) / 2
    upper_band = hl2 + (multiplier * atr)
    lower_band = hl2 - (multiplier * atr)

    # Initialize Supertrend and Trend Direction arrays
    supertrend_values = np.zeros_like(close)
    trend_direction = np.ones_like(close)  # Start with an uptrend assumption

    # Compute Supertrend values and Trend direction
    for i in range(1, len(close)):
        # Set trend direction based on the previous day's close
        if close[i] > upper_band[i - 1]:
            trend_direction[i] = 1  # Uptrend
        elif close[i] < lower_band[i - 1]:
            trend_direction[i] = -1  # Downtrend
            # print(f"Downtrend detected at i={i}")  # Debugging output
        else:
            trend_direction[i] = trend_direction[i - 1]  # Keep previous trend

        # Set Supertrend value based on trend direction
        if trend_direction[i] > 0:
            supertrend_values[i] = (
                max(lower_band[i], supertrend_values[i - 1])
                if supertrend_values[i - 1]
                else lower_band[i]
            )
        else:
            supertrend_values[i] = (
                min(upper_band[i], supertrend_values[i - 1])
                if supertrend_values[i - 1]
                else upper_band[i]
            )

    return supertrend_values, trend_direction
