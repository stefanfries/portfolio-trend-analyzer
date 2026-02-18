"""Configuration for trend detection algorithms.

This module provides configuration parameters optimized for different timeframes
(hourly vs daily candles) and volatile instruments like options/warrants.

Note: Trading hours are 08:00-22:00 (14 hours/day), 5 days/week.
      Therefore: 14 periods = 1 trading day, 70 periods = 1 week
"""

# Hourly candle configuration (14 days ≈ 196 hourly periods)
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

# Daily candle configuration (1 month ≈ 22 trading days)
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


def get_config(timeframe: str = "hourly") -> dict:
    """Get configuration for specified timeframe.

    Args:
        timeframe: String indicating timeframe ('hourly', 'hour', 'daily', 'day')

    Returns:
        Dictionary containing configuration parameters for the specified timeframe

    Example:
        >>> config = get_config('hourly')
        >>> config['supertrend_atr_period']
        7
    """
    configs = {
        "hourly": HOURLY_CONFIG,
        "hour": HOURLY_CONFIG,
        "daily": DAILY_CONFIG,
        "day": DAILY_CONFIG,
    }
    return configs.get(timeframe.lower(), HOURLY_CONFIG)
