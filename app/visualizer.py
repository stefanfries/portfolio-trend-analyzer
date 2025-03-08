import matplotlib
import mplfinance as mpf
import pandas as pd

matplotlib.use("Agg")  # Use non-interactive backend (Agg)
matplotlib.use("TkAgg")  # Use simple interactive backend (TkAgg)

print(matplotlib.get_backend())


def plot_candlestick(df: pd.DataFrame, title: str = "Candlestick Chart") -> None:
    """Plot a candlestick chart for the given security data."""

    df = df.set_index("datetime")  # Make the datetime column an index
    if "volume" in df.columns and df["volume"].nunique() == 1:
        df["volume"] += 1  # Avoids singular transformation error

    df = df.sort_index(ascending=True)

    mpf.plot(
        data=df,
        # mav=(5, 10),
        type="candle",
        # show_nontrading=True,
        # volume=True,
        style="charles",
        title=title,
        # savefig="candlestick.png",
    )
    print("📊 Chart saved as candlestick.png. Open it manually to view.")
