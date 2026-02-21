import numpy as np
import pandas as pd
import talib

from app.indicators import supertrend
from app.trend_config import get_config


def detect_trend_break(df: pd.DataFrame, timeframe: str = "hourly") -> dict:
    """Detect significant trend breaks using multi-indicator analysis.

    Combines Supertrend, ADX, directional indicators, and ATR-based volatility
    filtering to identify significant trend breaks (>20-30%) while filtering
    out normal market noise (<20%).

    Args:
        df: DataFrame with OHLC data (columns: high, low, close, datetime)
        timeframe: 'hourly' or 'daily' - determines which config to use

    Returns:
        Dictionary containing:
            - action: 'SELL', 'STRONG_SELL', 'BUY', or 'HOLD'
            - reason: Detailed explanation of the signal
            - confidence: 'HIGH', 'MEDIUM', or 'LOW'
            - metrics: Dict of all calculated indicators
            - timestamp: When signal was generated

    Example:
        >>> signal = detect_trend_break(df, timeframe='hourly')
        >>> print(f"{signal['action']}: {signal['reason']}")
    """
    # Get configuration
    config = get_config(timeframe)

    # Extract data - supertrend needs Series, ta-lib needs numpy arrays
    high_series = df["high"]
    low_series = df["low"]
    close_series = df["close"]

    high = high_series.to_numpy()
    low = low_series.to_numpy()
    close = close_series.to_numpy()
    current_price = close[-1]

    # 1. Calculate Supertrend (pass Series)
    st_values, st_direction = supertrend(
        high_series,
        low_series,
        close_series,
        atr_period=config["supertrend_atr_period"],
        multiplier=config["supertrend_multiplier"],
    )
    supertrend_signal = st_direction[-1]  # 1 = uptrend, -1 = downtrend

    # 2. Calculate ADX and Directional Indicators (use numpy arrays)
    adx = talib.ADX(high, low, close, timeperiod=config["adx_period"])
    plus_di = talib.PLUS_DI(high, low, close, timeperiod=config["adx_period"])
    minus_di = talib.MINUS_DI(high, low, close, timeperiod=config["adx_period"])

    adx_value = adx[-1]
    plus_di_value = plus_di[-1]
    minus_di_value = minus_di[-1]

    # 3. Calculate ATR and normalize to percentage
    atr = talib.ATR(high, low, close, timeperiod=config["atr_period"])
    atr_pct = (atr[-1] / current_price) * 100

    # 4. Calculate drawdowns and rallies
    # For short-term instruments (options/warrants), use all available data
    # or lookback window, whichever is smaller
    lookback = min(config["lookback_window"], len(high))
    recent_high = np.max(high[-lookback:]) if lookback > 0 else high[-1]
    recent_low = np.min(low[-lookback:]) if lookback > 0 else low[-1]

    drawdown_pct = ((current_price - recent_high) / recent_high) * 100
    rally_pct = ((current_price - recent_low) / recent_low) * 100

    # 5. Optional: EMA confirmation
    ema_fast_value = None
    ema_slow_value = None
    ema_signal = None

    if config["use_ema_confirmation"]:
        ema_fast = talib.EMA(close, timeperiod=config["ema_fast_period"])
        ema_slow = talib.EMA(close, timeperiod=config["ema_slow_period"])
        ema_fast_value = ema_fast[-1]
        ema_slow_value = ema_slow[-1]
        ema_signal = "bullish" if ema_fast_value > ema_slow_value else "bearish"

    # 6. Dynamic threshold adjustment (if enabled)
    min_threshold = config["min_threshold"]
    severe_threshold = config["severe_threshold"]

    if config["use_dynamic_thresholds"]:
        # Calculate recent volatility
        returns = np.diff(close) / close[:-1]
        recent_volatility = np.std(returns[-20:]) if len(returns) >= 20 else np.std(returns)
        historical_std = np.std(returns[-100:]) if len(returns) >= 100 else np.std(returns)
        high_vol_threshold = historical_std * 1.5  # Simplified threshold

        # Adjust thresholds if in high volatility regime
        if recent_volatility > high_vol_threshold:
            min_threshold *= 1.25  # Increase threshold by 25% during high volatility
            severe_threshold *= 1.25

    # 7. Generate signals based on combined conditions
    action = "HOLD"
    reason = ""
    confidence = "LOW"

    # STRONG_SELL conditions
    if drawdown_pct < -severe_threshold:
        action = "STRONG_SELL"
        reason = f"Critical drawdown of {drawdown_pct:.1f}% from recent high (€{recent_high:.2f}). Price crashed from €{recent_high:.2f} to €{current_price:.2f}."
        confidence = "HIGH"

    elif (
        drawdown_pct < -min_threshold
        and supertrend_signal == -1
        and adx_value > config["min_adx_strength"]
        and minus_di_value > plus_di_value
    ):
        # Check for very strong trend
        if adx_value > 40 and (minus_di_value - plus_di_value) > 15:
            action = "STRONG_SELL"
            confidence = "HIGH"
            reason = f"Strong downtrend confirmed: {drawdown_pct:.1f}% drawdown, ADX={adx_value:.1f} (very strong), Supertrend bearish, strong negative momentum (MinusDI={minus_di_value:.1f} > PlusDI={plus_di_value:.1f})."
        else:
            # Regular SELL
            action = "SELL"
            confidence = "HIGH" if adx_value > 35 else "MEDIUM"
            reason = f"Significant drawdown of {drawdown_pct:.1f}% with confirmed downtrend: ADX={adx_value:.1f} (strong trend), Supertrend bearish, negative momentum (MinusDI={minus_di_value:.1f} > PlusDI={plus_di_value:.1f})."

        # Add EMA confirmation if available
        if config["use_ema_confirmation"] and ema_signal == "bearish":
            reason += f" EMA crossover confirms bearish trend (EMA{config['ema_fast_period']}={ema_fast_value:.2f} < EMA{config['ema_slow_period']}={ema_slow_value:.2f})."

    # BUY conditions
    elif (
        rally_pct > min_threshold
        and supertrend_signal == 1
        and adx_value > config["min_adx_strength"]
        and plus_di_value > minus_di_value
    ):
        action = "BUY"
        confidence = "HIGH" if adx_value > 35 else "MEDIUM"
        reason = f"Strong rally of {rally_pct:.1f}% from recent low (€{recent_low:.2f}) with confirmed uptrend: ADX={adx_value:.1f}, Supertrend bullish, positive momentum (PlusDI={plus_di_value:.1f} > MinusDI={minus_di_value:.1f})."

        if config["use_ema_confirmation"] and ema_signal == "bullish":
            reason += " EMA crossover confirms bullish trend."

    # HOLD conditions (default)
    else:
        action = "HOLD"
        # Determine reason for holding
        if abs(drawdown_pct) < min_threshold and abs(rally_pct) < min_threshold:
            reason = f"No significant price movement. Drawdown: {drawdown_pct:.1f}%, Rally: {rally_pct:.1f}% (threshold: {min_threshold:.0f}%)."
        elif adx_value < config["min_adx_strength"]:
            reason = f"Weak trend (ADX={adx_value:.1f} < {config['min_adx_strength']}). Market is ranging/choppy. Wait for clearer direction."
            confidence = "LOW"
        else:
            reason = f"Mixed signals. Supertrend={'bullish' if supertrend_signal == 1 else 'bearish'}, but price movement insufficient for high-confidence signal."
            confidence = "LOW"

    # Compile all metrics
    metrics = {
        "supertrend_direction": int(supertrend_signal),
        "supertrend_value": float(st_values[-1]),
        "adx": float(adx_value),
        "plus_di": float(plus_di_value),
        "minus_di": float(minus_di_value),
        "drawdown_pct": float(drawdown_pct),
        "rally_pct": float(rally_pct),
        "atr_pct": float(atr_pct),
        "recent_high": float(recent_high),
        "recent_low": float(recent_low),
        "current_price": float(current_price),
    }

    # Add EMA metrics if used
    if config["use_ema_confirmation"]:
        metrics["ema_fast"] = float(ema_fast_value)
        metrics["ema_slow"] = float(ema_slow_value)
        metrics["ema_signal"] = ema_signal

    return {
        "action": action,
        "reason": reason,
        "confidence": confidence,
        "metrics": metrics,
        "timestamp": pd.Timestamp.now(),
    }
