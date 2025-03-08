import matplotlib.dates as mdates
import numpy as np
import pandas as pd


def fit_parabola(df: pd.DataFrame, no_of_values: int = 20) -> dict:
    """Fit a quadratic polynomial (parabola) to the last 'no_of_values" closing prices."""

    # Use the last 'no_of_values' closing prices for the analysis
    # recent_data = df.tail(no_of_values)

    df["mdates"] = df["datetime"].apply(mdates.date2num)
    # More precise numeric format for polyfit

    # Now you can use the 'mdates' column for polyfit
    x = df["mdates"].values  # Numeric values for polyfit (mdates)
    y = df["close"].values  # Security prices

    # Fit a parabola (2nd-degree polynomial)
    coeffs = np.polyfit(x, y, 2)
    a, b, c = coeffs

    # Compute the vertex of the parabola
    vertex_x = -b / (2 * a)
    vertex_y = np.polyval(coeffs, vertex_x)

    # Convert vertex_x (the mdates value) back to datetime format
    # vertex_date = mdates.num2date(vertex_x)  # Convert mdates back to datetime
    # return {"a": a, "b": b, "c": c, "vertex_date": vertex_date, "vertex_y": vertex_y}

    return {"a": a, "b": b, "c": c, "vertex_x": vertex_x, "vertex_y": vertex_y}


def generate_recommendation(parabola_parms: dict) -> str:
    """Generate buy/sell recommendations based on the parabola analysis."""

    # Unpack the parabola parameters
    a, b, c, vertex_x, vertex_y = parabola_parms.values()

    # Get current date in mdates format
    mdate_current_x = mdates.date2num(pd.Timestamp.today())

    # Check if trend is currently increasing (parabola derivative: 2*a + b > 0)
    trend_increasing = 2 * a * mdate_current_x + b > 0

    if vertex_x < mdate_current_x and trend_increasing:
        return f"BUY ASAP! Trend is increasing, minimum at {vertex_y:.2f} € was in the past ({mdates.num2date(vertex_x).strftime('%d.%m.%Y')})."
    elif vertex_x > mdate_current_x and not trend_increasing:
        return f"Place LIMITED BUY order at {vertex_y:.2f} €. Trend is decreasing, minimum expected in near future ({mdates.num2date(vertex_x).strftime('%d.%m.%Y')})."
    elif vertex_x < mdate_current_x and not trend_increasing:
        return f"SELL ASAP! Trend is decreasing, maximum at {vertex_y:.2f} € was in the past ({mdates.num2date(vertex_x).strftime('%d.%m.%Y')})."
    elif vertex_x > mdate_current_x and trend_increasing:
        return f"Place LIMITED SELL order at {vertex_y:.2f} €. Trend is increasing, maximum expected in the future ({mdates.num2date(vertex_x).strftime('%d.%m.%Y')})."

    return "No clear recommendation."
