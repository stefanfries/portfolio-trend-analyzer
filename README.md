# Portfolio Trend Analyzer

Advanced trend detection and analysis system for options and warrants trading with multi-indicator confirmation.

## Features

### ✅ Current Capabilities

- **Multi-Indicator Trend Detection**: Combines Supertrend, ADX, directional indicators, ATR, and EMAs
- **Volatility-Adjusted Thresholds**: Adapts to market conditions automatically
- **Parabola Fitting Analysis**: Traditional trend prediction using polynomial fitting
- **Automated Chart Generation**: Candlestick charts for all analyzed securities
- **Console Progress Tracking**: Real-time status updates during analysis
- **Configurable Timeframes**: Optimized parameters for hourly and daily data

### 🎯 Signal Types

- **STRONG_SELL**: Severe drawdowns (>30%) or critical trend breaks
- **SELL**: Significant drawdowns (>20%) with confirmed downtrend
- **BUY**: Strong rallies (>20%) with confirmed uptrend  
- **HOLD**: Mixed signals or ranging market

### 📊 Technical Indicators

- **Supertrend**: Trend direction with ATR-based bands
- **ADX (Average Directional Index)**: Trend strength measurement
- **Plus/Minus DI**: Directional movement indicators
- **ATR (Average True Range)**: Volatility normalization
- **EMA Crossovers**: 8/21 period confirmation filter
- **Drawdown/Rally Detection**: From rolling highs/lows

## Recent Updates (2026-02-10)

### 🚨 Critical Bug Fixes

- **Data Ordering**: Fixed reverse chronological data from API causing stale price calculations
- **Threshold Logic**: Corrected percentage comparisons (removed 100x multiplication error)
- **Lookback Window**: Extended from 20 to 240 hours for proper trend capture
- **Type Handling**: Fixed pandas Series vs numpy array operations

### ✨ New Features

- Trend detection system with 4-level signal confidence
- Debug output showing data validation (highs/lows/current)
- Windows console UTF-8 encoding for emoji support
- Configuration-driven parameters (trend_config.py)

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

## Configuration

Edit `app/main.py` to select your depot:

```python
depot = mega_trend_folger  # or test_depot, etf_depot, etc.
```

Adjust parameters in `app/trend_config.py`:

- Lookback windows
- Threshold percentages  
- ADX minimum strength
- EMA periods

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
│   ├── models.py            # Data models
│   └── settings.py          # API settings
├── docs/
│   ├── IMPLEMENTATION_PLAN.md       # Roadmap and architecture
│   └── SESSION_NOTES_2026-02-10.md  # Development log
└── README.md                # This file
```

## Development Roadmap

### Phase 1: Core Algorithm ✅ (In Progress - 37.5% complete)

- ✅ Configuration system
- ✅ Multi-indicator trend detection
- ✅ Main loop integration
- ⏳ Enhanced email reporting
- ⏳ Logging system
- ⏳ Testing & validation

### Phase 2: MongoDB Integration (Planned)

- Fetch instruments from database
- Store analysis results
- Track recommendation history
- Portfolio synchronization

### Phase 3: Cloud Deployment (Planned)

- Docker containerization
- Azure deployment
- Automated scheduling
- Email notifications

### Phase 4: Production Features (Planned)

- Web dashboard
- SMS alerts
- Performance tracking
- Backtesting framework

## Algorithm Validation

Recent analysis of 17 securities showed:

- **11 STRONG_SELL** signals (65%) - correctly identified major crashes
- **1 BUY** signal (6%) - confirmed strong uptrend
- **5 HOLD** signals (29%) - ranging markets or weak trends

**vs Parabola Fitting:**

- Found 4 catastrophic cases where parabola said "BUY" but securities had -35% to -90% drawdowns
- Trend detection correctly filtered noise with ADX strength requirements

## License

See LICENSE file for details.

## Contributing

This is a personal trading tool. For collaboration or questions, please open an issue.

---

**⚠️ Disclaimer**: This tool is for educational and personal use only. Always perform your own analysis and consult a financial advisor before making investment decisions.
