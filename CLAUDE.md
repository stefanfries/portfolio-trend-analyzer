# Portfolio Trend Analyzer

Multi-indicator trend detection system for options and warrants trading.
Detects significant trend breaks using Supertrend, ADX, EMAs, and ATR, and generates
buy/sell/hold/strong-sell signals with volatility-adjusted thresholds.

## How to run

```bash
uv sync
uv run python -m app.main
```

## Architecture

- `app/main.py` — main analysis loop
- `app/analysis.py` — trend detection and parabola fitting
- `app/trend_config.py` — algorithm parameters (differs per timeframe and instrument type)
- `app/indicators.py` — Supertrend calculation
- `app/reader.py` — fetches OHLCV data from Comdirect API
- `app/visualizer.py` — mplfinance candlestick chart generation → `charts/`
- `app/results_saver.py` — Excel export → `results/`
- `app/depots.py` — portfolio definitions (tickers, WKNs, ISINs)
- `app/signal_history.py` — persistent signal tracking (prevents duplicate signals)
- `app/notifier.py` — email notifications

## Signal logic

| Signal | Condition |
|--------|-----------|
| `STRONG_SELL` | Drawdown > 30% |
| `SELL` | Drawdown > 20% |
| `BUY` | Rally > 20% |
| `HOLD` | Mixed indicators |

Thresholds are volatility-adjusted via ATR — don't hardcode fixed percentages.

## Configuration

- **Timeframe:** `'hourly'` or `'daily'` — affects indicator periods (14-period hourly ≈ 1 trading day, 140-period ≈ 10 days)
- **Instrument type:** `'stock'` or `'warrant'` (warrants need more sensitive thresholds)
- **Portfolios:** defined in `app/depots.py` (mega_trend_folger, tsi_6i_aktien, test_depot, etc.)
- **Force-save:** override market hours detection for testing outside trading hours

## Key behaviours

- Signal history prevents duplicate signals for the same instrument + timeframe combination
- "Official run" = after market close (after 22:00 German time); weekends use Friday's session
- TA-Lib binary must be installed on the platform before `uv sync` (same as candlestick-screener)
- Data source: Comdirect API via `app/reader.py` — requires valid Comdirect credentials in `.env`
