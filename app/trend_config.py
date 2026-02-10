"""Configuration for trend detection algorithms.

This module provides configuration parameters optimized for different timeframes
(hourly vs daily candles) and volatile instruments like options/warrants.
"""

# Hourly candle configuration (14 days ≈ 336 periods)
HOURLY_CONFIG = {
    # Supertrend parameters - optimized for fast reaction
    "supertrend_atr_period": 7,  # Fast reaction for volatile instruments
    "supertrend_multiplier": 3.5,  # Wider bands to reduce false signals
    # ADX trend strength parameters
    "adx_period": 10,  # Shorter period for hourly data
    "atr_period": 14,  # Standard ATR period
    # Drawdown/Rally detection
    "lookback_window": 240,  # Periods to find recent high/low (~10 days for hourly)
    # Signal thresholds (in percentage)
    "min_threshold": 20.0,  # 20% - significant move
    "severe_threshold": 30.0,  # 30% - critical move
    "min_adx_strength": 25,  # Minimum ADX for "strong trend"
    # Optional EMA confirmation
    "use_ema_confirmation": True,
    "ema_fast_period": 8,  # ~1 trading day
    "ema_slow_period": 21,  # ~2.5 trading days
    # Volatility adjustment
    "use_dynamic_thresholds": True,
    "volatility_quantile": 0.75,  # 75th percentile for high volatility detection
}

# Daily candle configuration (1 month ≈ 22 periods)
DAILY_CONFIG = {
    "supertrend_atr_period": 10,
    "supertrend_multiplier": 3.0,
    "adx_period": 14,
    "atr_period": 14,
    "lookback_window": 10,  # ~2 weeks
    "min_threshold": 20.0,  # 20% threshold
    "severe_threshold": 30.0,  # 30% threshold
    "min_adx_strength": 25,
    "use_ema_confirmation": True,
    "ema_fast_period": 5,
    "ema_slow_period": 13,
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
