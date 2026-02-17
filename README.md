# Portfolio Trend Analyzer

Advanced trend detection and analysis system for options and warrants trading with multi-indicator confirmation.

## Features

- **Multi-Indicator Trend Detection**: Combines Supertrend, ADX, directional indicators, ATR, and EMAs
- **Volatility-Adjusted Thresholds**: Adapts to market conditions automatically
- **Parabola Fitting Analysis**: Traditional trend prediction using polynomial fitting
- **Automated Chart Generation**: Candlestick charts for all analyzed securities
- **Console Progress Tracking**: Real-time status updates during analysis
- **Configurable Timeframes**: Optimized parameters for hourly and daily data
- **Excel Export**: Saves analysis results with proper formatting

### Signal Types

- **STRONG_SELL**: Severe drawdowns (>30%) or critical trend breaks
- **SELL**: Significant drawdowns (>20%) with confirmed downtrend
- **BUY**: Strong rallies (>20%) with confirmed uptrend  
- **HOLD**: Mixed signals or ranging market

### Technical Indicators

- **Supertrend**: Trend direction with ATR-based bands
- **ADX (Average Directional Index)**: Trend strength measurement
- **Plus/Minus DI**: Directional movement indicators
- **ATR (Average True Range)**: Volatility normalization
- **EMA Crossovers**: 8/21 period confirmation filter
- **Drawdown/Rally Detection**: From rolling highs/lows

## Installation

```bash
# Clone the repository
git clone https://github.com/stefanfries/portfolio-trend-analyzer.git
cd portfolio-trend-analyzer

# Install dependencies using uv
uv sync

# Run analysis
uv run python -m app.main
```

## Usage

Run the analysis on your selected depot:

```bash
uv run python -m app.main
```

The application will:
1. Fetch current price data for all securities in the selected depot
2. Perform trend analysis using multiple indicators
3. Generate buy/sell/hold recommendations
4. Create candlestick charts in the `charts/` folder
5. Save results to Excel in the `results/` folder

## Configuration

### Select Portfolio

Edit [app/main.py](app/main.py) to choose your depot:

```python
depot = mega_trend_folger  # or test_depot, etf_depot, etc.
depot_name = "mega_trend_folger"
```

### Adjust Algorithm Parameters

Edit [app/trend_config.py](app/trend_config.py) to customize:

- Lookback windows for trend detection
- Threshold percentages for buy/sell signals  
- ADX minimum strength requirements
- EMA periods for trend confirmation

## Project Structure

```text
portfolio-trend-analyzer/
├── app/
│   ├── main.py              # Main analysis loop
│   ├── analysis.py          # Trend detection & parabola fitting
│   ├── trend_config.py      # Algorithm parameters
│   ├── indicators.py        # Technical indicators (Supertrend)
│   ├── reader.py            # API data fetching
│   ├── visualizer.py        # Chart generation
│   ├── depots.py            # Portfolio definitions
│   ├── results_saver.py     # Excel export
│   ├── models.py            # Data models
│   ├── settings.py          # API settings
│   └── notifier.py          # Email notifications
├── charts/                  # Generated candlestick charts
├── results/                 # Excel analysis results
├── docs/
│   ├── IMPLEMENTATION_PLAN.md       # Development roadmap
│   ├── ALGORITHM_VALIDATION.md      # Performance metrics
│   └── SESSION_NOTES_2026-02-10.md  # Development log
└── README.md                # This file
```

## Documentation

- **[IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md)**: Development roadmap and architecture
- **[ALGORITHM_VALIDATION.md](docs/ALGORITHM_VALIDATION.md)**: Algorithm performance and validation results
- **[SESSION_NOTES_2026-02-10.md](docs/SESSION_NOTES_2026-02-10.md)**: Development log and bug fixes

## License

See LICENSE file for details.

## Contributing

This is a personal trading tool. For collaboration or questions, please open an issue.

---

**⚠️ Disclaimer**: This tool is for educational and personal use only. Always perform your own analysis and consult a financial advisor before making investment decisions.
