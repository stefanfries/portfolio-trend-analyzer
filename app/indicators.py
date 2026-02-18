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
    basic_upper_band = hl2 + (multiplier * atr)
    basic_lower_band = hl2 - (multiplier * atr)

    # Find first valid (non-NaN) index
    first_valid_idx = atr.first_valid_index()
    if first_valid_idx is None:
        # Return empty series if no valid data
        return pd.Series(index=close.index, dtype=float), pd.Series(index=close.index, dtype=float)

    first_valid = close.index.get_loc(first_valid_idx)

    # Initialize final bands with NaN
    final_upper_band = pd.Series(index=close.index, dtype=float)
    final_lower_band = pd.Series(index=close.index, dtype=float)

    # Set initial valid values
    final_upper_band.iloc[first_valid] = basic_upper_band.iloc[first_valid]
    final_lower_band.iloc[first_valid] = basic_lower_band.iloc[first_valid]

    # Calculate final bands with trailing logic
    for i in range(first_valid + 1, len(close)):
        # Final upper band - trails down, never goes up
        final_upper_band.iloc[i] = (
            basic_upper_band.iloc[i]
            if basic_upper_band.iloc[i] < final_upper_band.iloc[i - 1]
            or close.iloc[i - 1] > final_upper_band.iloc[i - 1]
            else final_upper_band.iloc[i - 1]
        )

        # Final lower band - trails up, never goes down
        final_lower_band.iloc[i] = (
            basic_lower_band.iloc[i]
            if basic_lower_band.iloc[i] > final_lower_band.iloc[i - 1]
            or close.iloc[i - 1] < final_lower_band.iloc[i - 1]
            else final_lower_band.iloc[i - 1]
        )

    # Initialize Supertrend and Trend Direction columns with NaN
    supertrend_values = pd.Series(index=close.index, dtype=float)
    trend_direction = pd.Series(index=close.index, dtype=float)

    # Set initial values
    supertrend_values.iloc[first_valid] = final_lower_band.iloc[first_valid]
    trend_direction.iloc[first_valid] = 1

    # Compute Supertrend values and Trend direction
    for i in range(first_valid + 1, len(close)):
        # Determine trend based on close vs previous Supertrend value
        if close.iloc[i] > supertrend_values.iloc[i - 1]:
            trend_direction.iloc[i] = 1  # Uptrend
            supertrend_values.iloc[i] = final_lower_band.iloc[i]
        elif close.iloc[i] < supertrend_values.iloc[i - 1]:
            trend_direction.iloc[i] = -1  # Downtrend
            supertrend_values.iloc[i] = final_upper_band.iloc[i]
        else:
            # Keep previous trend
            trend_direction.iloc[i] = trend_direction.iloc[i - 1]
            if trend_direction.iloc[i] > 0:
                supertrend_values.iloc[i] = final_lower_band.iloc[i]
            else:
                supertrend_values.iloc[i] = final_upper_band.iloc[i]

    return supertrend_values, trend_direction


def supertrend(high, low, close, atr_period=7, multiplier=3.0) -> tuple[np.ndarray, np.ndarray]:
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
    basic_upper_band = hl2 + (multiplier * atr)
    basic_lower_band = hl2 - (multiplier * atr)

    # Find first valid (non-NaN) index
    first_valid = atr_period  # ATR returns NaN for first atr_period values

    # Initialize final bands with NaN
    final_upper_band = np.full_like(close, np.nan)
    final_lower_band = np.full_like(close, np.nan)

    # Set initial valid values
    if first_valid < len(close):
        final_upper_band[first_valid] = basic_upper_band[first_valid]
        final_lower_band[first_valid] = basic_lower_band[first_valid]

        # Calculate final bands with trailing logic
        for i in range(first_valid + 1, len(close)):
            # Final upper band - trails down, never goes up
            final_upper_band[i] = (
                basic_upper_band[i]
                if basic_upper_band[i] < final_upper_band[i - 1]
                or close[i - 1] > final_upper_band[i - 1]
                else final_upper_band[i - 1]
            )

            # Final lower band - trails up, never goes down
            final_lower_band[i] = (
                basic_lower_band[i]
                if basic_lower_band[i] > final_lower_band[i - 1]
                or close[i - 1] < final_lower_band[i - 1]
                else final_lower_band[i - 1]
            )

    # Initialize Supertrend and Trend Direction arrays with NaN
    supertrend_values = np.full_like(close, np.nan)
    trend_direction = np.full_like(close, np.nan)

    # Set initial values at first valid index
    if first_valid < len(close):
        supertrend_values[first_valid] = final_lower_band[first_valid]
        trend_direction[first_valid] = 1

        # Compute Supertrend values and Trend direction
        for i in range(first_valid + 1, len(close)):
            # Determine trend based on close vs previous Supertrend value
            if close[i] > supertrend_values[i - 1]:
                trend_direction[i] = 1  # Uptrend
                supertrend_values[i] = final_lower_band[i]
            elif close[i] < supertrend_values[i - 1]:
                trend_direction[i] = -1  # Downtrend
                supertrend_values[i] = final_upper_band[i]
            else:
                # Keep previous trend
                trend_direction[i] = trend_direction[i - 1]
                if trend_direction[i] > 0:
                    supertrend_values[i] = final_lower_band[i]
                else:
                    supertrend_values[i] = final_upper_band[i]

    return supertrend_values, trend_direction
