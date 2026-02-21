"""Configuration for trend detection algorithms.

This module provides configuration parameters optimized for different timeframes
(hourly vs daily candles) and instrument types (stocks vs warrants/options).

Note: Trading hours are 08:00-22:00 (14 hours/day), 5 days/week.
      Therefore: 14 periods = 1 trading day, 70 periods = 1 week
"""

# ============================================================================
# WARRANT/OPTIONS CONFIGURATIONS (High volatility instruments)
# ============================================================================

# Hourly candle configuration for warrants (14 days ≈ 196 hourly periods)
HOURLY_CONFIG = {
    # Supertrend parameters - optimized for balanced reaction
    "supertrend_atr_period": 14,  # 1 trading day - standard ATR calculation
    "supertrend_multiplier": 3.5,  # Wider bands to reduce false signals
    # ADX trend strength parameters
    "adx_period": 14,  # 1 trading day - standard ADX calculation
    "atr_period": 14,  # 1 trading day - standard ATR period
    # Drawdown/Rally detection
    "lookback_window": 140,  # 10 trading days (2 weeks) for trend detection
    # Signal thresholds (in percentage)
    "min_threshold": 20.0,  # 20% - significant move
    "severe_threshold": 30.0,  # 30% - critical move
    "min_adx_strength": 25,  # Minimum ADX for "strong trend"
    # Optional EMA confirmation
    "use_ema_confirmation": True,
    "ema_fast_period": 14,  # 1 trading day - daily trend
    "ema_slow_period": 42,  # 3 trading days - multi-day trend
    # Volatility adjustment
    "use_dynamic_thresholds": True,
    "volatility_quantile": 0.75,  # 75th percentile for high volatility detection
}

# Daily candle configuration for warrants (1 month ≈ 22 trading days)
DAILY_CONFIG = {
    "supertrend_atr_period": 10,  # 10 trading days - standard for daily
    "supertrend_multiplier": 3.0,
    "adx_period": 14,  # 14 trading days - standard ADX calculation
    "atr_period": 14,  # 14 trading days - standard ATR period
    "lookback_window": 10,  # 10 trading days (2 weeks)
    "min_threshold": 20.0,  # 20% threshold
    "severe_threshold": 30.0,  # 30% threshold
    "min_adx_strength": 25,
    "use_ema_confirmation": True,
    "ema_fast_period": 5,  # 5 trading days (1 week)
    "ema_slow_period": 13,  # 13 trading days (~2.5 weeks)
    "use_dynamic_thresholds": True,
    "volatility_quantile": 0.75,
}

# ============================================================================
# STOCK CONFIGURATIONS (Lower volatility, more sensitive thresholds)
# ============================================================================

# Hourly candle configuration for stocks
STOCK_HOURLY_CONFIG = {
    # Supertrend parameters
    "supertrend_atr_period": 14,  # 1 trading day - standard ATR calculation
    "supertrend_multiplier": 3.0,  # Slightly tighter bands for stocks
    # ADX trend strength parameters
    "adx_period": 14,  # 1 trading day - standard ADX calculation
    "atr_period": 14,  # 1 trading day - standard ATR period
    # Drawdown/Rally detection
    "lookback_window": 140,  # 10 trading days (2 weeks) for trend detection
    # Signal thresholds (in percentage) - MUCH LOWER for stocks
    "min_threshold": 5.0,  # 5% - significant move for a stock
    "severe_threshold": 10.0,  # 10% - critical move for a stock
    "min_adx_strength": 20,  # Slightly lower ADX threshold
    # Optional EMA confirmation
    "use_ema_confirmation": True,
    "ema_fast_period": 14,  # 1 trading day - daily trend
    "ema_slow_period": 42,  # 3 trading days - multi-day trend
    # Volatility adjustment
    "use_dynamic_thresholds": True,
    "volatility_quantile": 0.75,  # 75th percentile for high volatility detection
}

# Daily candle configuration for stocks
STOCK_DAILY_CONFIG = {
    "supertrend_atr_period": 10,  # 10 trading days - standard for daily
    "supertrend_multiplier": 2.5,  # Tighter for stocks
    "adx_period": 14,  # 14 trading days - standard ADX calculation
    "atr_period": 14,  # 14 trading days - standard ATR period
    "lookback_window": 20,  # 20 trading days (1 month)
    "min_threshold": 5.0,  # 5% threshold for stocks
    "severe_threshold": 10.0,  # 10% threshold for stocks
    "min_adx_strength": 20,
    "use_ema_confirmation": True,
    "ema_fast_period": 5,  # 5 trading days (1 week)
    "ema_slow_period": 13,  # 13 trading days (~2.5 weeks)
    "use_dynamic_thresholds": True,
    "volatility_quantile": 0.75,
}


def get_config(timeframe: str = "hourly", instrument_type: str = "warrant") -> dict:
    """Get configuration for specified timeframe and instrument type.

    Args:
        timeframe: String indicating timeframe ('hourly', 'hour', 'daily', 'day')
        instrument_type: String indicating instrument type ('stock', 'warrant', 'option')

    Returns:
        Dictionary containing configuration parameters for the specified
        timeframe and instrument type

    Examples:
        >>> config = get_config('hourly', 'stock')
        >>> config['min_threshold']
        5.0
        >>> config = get_config('hourly', 'warrant')
        >>> config['min_threshold']
        20.0
    """
    # Normalize inputs
    timeframe = timeframe.lower()
    instrument_type = instrument_type.lower()

    # Map 'option' to 'warrant' (same volatility profile)
    if instrument_type in ["option", "options"]:
        instrument_type = "warrant"

    # Configuration lookup table
    configs = {
        ("hourly", "warrant"): HOURLY_CONFIG,
        ("hour", "warrant"): HOURLY_CONFIG,
        ("daily", "warrant"): DAILY_CONFIG,
        ("day", "warrant"): DAILY_CONFIG,
        ("hourly", "stock"): STOCK_HOURLY_CONFIG,
        ("hour", "stock"): STOCK_HOURLY_CONFIG,
        ("daily", "stock"): STOCK_DAILY_CONFIG,
        ("day", "stock"): STOCK_DAILY_CONFIG,
    }

    # Return config with fallback to warrant hourly config
    return configs.get((timeframe, instrument_type), HOURLY_CONFIG)
