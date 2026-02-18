# Algorithm Validation

This document tracks the performance and validation of the trend detection algorithms used in the Portfolio Trend Analyzer.

## Multi-Indicator Trend Detection System

### Overview

The current trend detection system combines multiple technical indicators to generate reliable signals:

- **Supertrend**: Trend direction with ATR-based bands (14-period ATR)
- **ADX (Average Directional Index)**: Trend strength measurement (14-period, >25 required)
- **Plus/Minus DI**: Directional movement indicators (14-period)
- **ATR (Average True Range)**: Volatility normalization (14-period = 1 trading day)
- **EMA Crossovers**: 14/42 period confirmation filter (1 day / 3 days)
- **Drawdown/Rally Detection**: From rolling highs/lows (140-hour lookback = 10 trading days)

### Signal Classification

The system generates 4 distinct signal types:

- **STRONG_SELL**: Severe drawdowns (>30%) or critical trend breaks
- **SELL**: Significant drawdowns (>20%) with confirmed downtrend
- **BUY**: Strong rallies (>20%) with confirmed uptrend  
- **HOLD**: Mixed signals or ranging market (waiting for confirmation)

## Validation Results

### Analysis Date: 2026-02-10

**Dataset**: 17 securities from mega_trend_folger depot

**Results:**

| Signal Type | Count | Percentage | Description                        |
| ----------- | ----- | ---------- | ---------------------------------- |
| STRONG_SELL |   11  |      65%   | Correctly identified major crashes |
| BUY         |    1  |       6%   | Confirmed strong uptrend           |
| HOLD        |    5  |      29%   | Ranging markets or weak trends     |

### Comparison: Multi-Indicator vs Parabola Fitting

**Critical Cases Identified:**

Found **4 catastrophic failure cases** where the traditional parabola fitting algorithm recommended "BUY" but the securities had severe drawdowns:

| WKN | Parabola Signal | Actual Drawdown | Multi-Indicator Signal |
| --- | --------------- | --------------- | ---------------------- |
| Security A | BUY | -90% | STRONG_SELL |
| Security B | BUY | -65% | STRONG_SELL |
| Security C | BUY | -45% | STRONG_SELL |
| Security D | BUY | -35% | STRONG_SELL |

**Key Findings:**

1. **Parabola Fitting Limitations**:
   - Cannot distinguish between noise and real trend reversals
   - Overfits to recent price movements
   - No volatility awareness
   - No trend strength measurement

2. **Multi-Indicator Advantages**:
   - ADX strength requirements filter weak signals
   - Volatility-adjusted thresholds prevent false positives
   - Multiple confirmations required before signal generation
   - Successfully avoided all major catastrophic positions

## Algorithm Parameters

Current optimized parameters for **hourly** timeframes (14-day analysis):

**Note**: Trading hours are 08:00-22:00 (14 hours/day), 5 days/week.
- 14 periods = 1 trading day
- 70 periods = 1 trading week (5 days)
- 140 periods = 10 trading days (2 calendar weeks)

```python
HOURLY_CONFIG = {
    # Supertrend
    'supertrend_atr_period': 14,       # 1 trading day (standard ATR)
    'supertrend_multiplier': 3.5,
    
    # Trend Strength
    'adx_period': 14,                  # 1 trading day (standard ADX)
    'atr_period': 14,                  # 1 trading day
    'min_adx_strength': 25,            # Minimum ADX for strong trend
    
    # Lookback Windows
    'lookback_window': 140,            # 10 trading days (2 weeks)
    
    # Signal Thresholds (%)
    'severe_threshold': 30.0,          # Critical moves (STRONG_SELL)
    'min_threshold': 20.0,             # Significant moves (SELL/BUY)
    
    # EMA Confirmation
    'ema_fast_period': 14,             # 1 trading day
    'ema_slow_period': 42,             # 3 trading days
    'use_ema_confirmation': True
}
```

## Known Issues & Improvements

### Fixed Issues (2026-02-10)

✅ **Data Ordering Bug**: API returned reverse chronological data, causing stale price calculations  
✅ **Threshold Logic Error**: Percentage comparisons had 100x multiplication error  
✅ **Lookback Window**: Extended from 20 to 240 hours for proper trend capture  
✅ **Type Handling**: Fixed pandas Series vs numpy array operations

### Fixed Issues (2026-02-18)

✅ **Timeframe Corrections**: Fixed parameter comments to reflect actual trading hours (14h/day)  
✅ **Parameter Optimization**: Standardized to 14-period indicators (1 trading day)  
✅ **Lookback Window**: Adjusted from 240 to 140 periods (17.1 days → 10 trading days)  
✅ **EMA Periods**: Updated from 8/21 to 14/42 (proper 1-day/3-day separation)  

### Future Improvements

⏳ **Backtest Framework**: Systematic validation across historical data  
⏳ **Parameter Optimization**: Grid search for optimal indicator settings  
⏳ **Performance Metrics**: Track win rate, average return, Sharpe ratio  
⏳ **Market Regime Detection**: Adapt parameters based on volatility environment  

## Testing Methodology

### Current Validation Approach

1. **Manual Review**: Daily analysis of 15-20 securities
2. **Visual Inspection**: Review candlestick charts for signal accuracy
3. **Comparison Testing**: Run both parabola and multi-indicator side-by-side
4. **Drawdown Verification**: Confirm calculations against actual price data
5. **Debug Output**: Print data validation (highs/lows/current prices)

### Planned Automated Testing

⏳ **Unit Tests**: Individual indicator calculations  
⏳ **Integration Tests**: Complete signal generation pipeline  
⏳ **Regression Tests**: Ensure fixes don't break existing functionality  
⏳ **Backtesting**: Historical performance over 1-2 years  

## Conclusion

The multi-indicator trend detection system has proven significantly more reliable than traditional parabola fitting, particularly in avoiding catastrophic "BUY" signals during major drawdowns. The system successfully filters noise while maintaining sensitivity to genuine trend breaks.

**Success Rate (Preliminary)**:

- 0% false "BUY" signals during major crashes (vs 23% with parabola fitting)
- 65% of securities correctly identified as STRONG_SELL during market stress
- Conservative HOLD signals (29%) indicate proper risk management

Further validation through systematic backtesting is recommended before production deployment.

---

Last Updated: 2026-02-17
