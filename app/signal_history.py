"""Signal history tracking for consecutive signal confirmation.

This module manages the persistence and analysis of daily signals to determine
when a trading action should be executed based on consecutive signal confirmation.

Signals are only persisted to disk after market close (22:00) to avoid polluting
the historical data with test runs during market hours.
"""

import json
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Literal

from app.settings import SignalHistorySettings

SignalAction = Literal["BUY", "SELL", "STRONG_SELL", "HOLD"]
Confidence = Literal["HIGH", "MEDIUM", "LOW"]
InstrumentType = Literal["stock", "warrant"]


class SignalHistoryManager:
    """Manages signal history tracking and execution recommendations."""

    def __init__(
        self,
        history_file: Path = Path("results") / "signal_history.json",
        market_close_time: time | None = None,
        retention_days: int | None = None,
    ):
        """Initialize the signal history manager.

        Args:
            history_file: Path to JSON file storing signal history
            market_close_time: Time after which signals are persisted (default from settings)
            retention_days: Number of days to retain signal history (default from settings)
        """
        self.settings = SignalHistorySettings()
        self.history_file = history_file
        self.market_close_time = market_close_time or time(
            self.settings.signal_history_market_close_hour,
            self.settings.signal_history_market_close_minute,
        )
        self.retention_days = retention_days or self.settings.signal_history_retention_days
        self.history = self._load_history()

    def _load_history(self) -> dict:
        """Load signal history from JSON file."""
        if not self.history_file.exists():
            return {}

        try:
            with open(self.history_file, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"⚠️ Warning: Could not load signal history: {e}")
            return {}

    def _save_history(self):
        """Save signal history to JSON file (atomic write)."""
        # Ensure results directory exists
        self.history_file.parent.mkdir(exist_ok=True)

        # Atomic write: write to temp file, then rename
        temp_file = self.history_file.with_suffix(".tmp")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
            temp_file.replace(self.history_file)
        except OSError as e:
            print(f"⚠️ Warning: Could not save signal history: {e}")
            if temp_file.exists():
                temp_file.unlink()

    def _get_current_trading_day(self, current_time: datetime | None = None) -> str:
        """Get the current trading day date (adjusts weekends to Friday).

        If current time is on a weekend, returns the previous Friday's date.
        This ensures we don't create duplicate signals on weekends.

        Args:
            current_time: Time to check (default: now)

        Returns:
            Date string in YYYY-MM-DD format for the current trading day
        """
        if current_time is None:
            current_time = datetime.now()

        # 0=Monday, 1=Tuesday, ..., 5=Saturday, 6=Sunday
        weekday = current_time.weekday()

        # If Saturday (5), go back 1 day to Friday
        if weekday == 5:
            trading_day = current_time - timedelta(days=1)
        # If Sunday (6), go back 2 days to Friday
        elif weekday == 6:
            trading_day = current_time - timedelta(days=2)
        else:
            # Weekday - use current date
            trading_day = current_time

        return trading_day.strftime("%Y-%m-%d")

    def is_after_market_close(self, current_time: datetime | None = None) -> bool:
        """Check if current time is after market close.

        Args:
            current_time: Time to check (default: now)

        Returns:
            True if after market close time
        """
        if current_time is None:
            current_time = datetime.now()

        return current_time.time() >= self.market_close_time

    def add_signal(
        self,
        wkn: str,
        action: SignalAction,
        confidence: Confidence,
        instrument_type: InstrumentType,
        force_save: bool = False,
        current_time: datetime | None = None,
    ) -> dict:
        """Add a new signal and determine if action should be executed.

        Args:
            wkn: Security identifier (WKN)
            action: Signal action (BUY, SELL, STRONG_SELL, HOLD)
            confidence: Signal confidence level
            instrument_type: Type of instrument (stock or warrant)
            force_save: Force save to disk even before market close
            current_time: Override current time (for testing)

        Returns:
            Dictionary with execution recommendation:
                - should_execute: bool
                - consecutive_days: int
                - required_days: int
                - reason: str
                - will_persist: bool (if this signal will be saved to disk)
        """
        if current_time is None:
            current_time = datetime.now()

        # Get the trading day (adjusts weekends to Friday)
        trading_day_str = self._get_current_trading_day(current_time)

        # Initialize WKN entry if not exists
        if wkn not in self.history:
            self.history[wkn] = {
                "signals": [],
                "instrument_type": instrument_type,
            }

        # Get signal history for this WKN
        wkn_history = self.history[wkn]

        # Update instrument type (may change if user reclassifies)
        wkn_history["instrument_type"] = instrument_type

        # Check if we already have a signal for this trading day
        signals = wkn_history["signals"]
        trading_day_signal_exists = any(s["date"] == trading_day_str for s in signals)

        # Determine if we should persist this signal
        will_persist = force_save or self.is_after_market_close(current_time)

        # Check if running on weekend
        is_weekend = current_time.weekday() >= 5  # 5=Saturday, 6=Sunday

        # Only add signal if:
        # - After market close (or forced)
        # - No signal exists yet for this trading day
        if will_persist and not trading_day_signal_exists:
            signals.append(
                {
                    "date": trading_day_str,
                    "action": action,
                    "confidence": confidence,
                }
            )

            # Keep only last N days (from settings)
            if len(signals) > self.retention_days:
                signals[:] = signals[-self.retention_days :]
        elif will_persist and trading_day_signal_exists and is_weekend:
            # Weekend run with existing Friday signal - don't persist
            will_persist = False

        # Determine required consecutive days
        required_days = self._get_required_days(action, instrument_type)

        # Count consecutive days of the same signal
        consecutive_days = self._count_consecutive_signals(wkn, action)

        # Determine if should execute
        should_execute = (
            consecutive_days >= required_days
            and action != "HOLD"
            and will_persist  # Only recommend execution for "official" runs
        )

        # Save if persisting
        if will_persist:
            self._save_history()

        # Build recommendation
        recommendation = {
            "should_execute": should_execute,
            "consecutive_days": consecutive_days,
            "required_days": required_days,
            "will_persist": will_persist,
            "reason": self._build_reason(
                action, consecutive_days, required_days, should_execute, will_persist, current_time
            ),
        }

        return recommendation

    def _get_required_days(self, action: SignalAction, instrument_type: InstrumentType) -> int:
        """Get required consecutive days for signal confirmation.

        Args:
            action: Signal action
            instrument_type: Type of instrument

        Returns:
            Number of consecutive days required
        """
        # STRONG_SELL: Immediate action after 1 day (capital protection)
        if action == "STRONG_SELL":
            return 1

        # Warrants: 2 days (high volatility, need confirmation but faster)
        if instrument_type == "warrant":
            return 2

        # Stocks: 3 days (lower volatility, can afford confirmation period)
        return 3

    def _count_consecutive_signals(self, wkn: str, action: SignalAction) -> int:
        """Count consecutive days of the same signal from most recent backwards.

        Args:
            wkn: Security identifier
            action: Action to count

        Returns:
            Number of consecutive days with same signal
        """
        if wkn not in self.history:
            return 0

        signals = self.history[wkn]["signals"]
        if not signals:
            return 0

        # Count backwards from most recent
        count = 0
        for signal in reversed(signals):
            if signal["action"] == action:
                count += 1
            else:
                break

        return count

    def _build_reason(
        self,
        action: SignalAction,
        consecutive_days: int,
        required_days: int,
        should_execute: bool,
        will_persist: bool,
        current_time: datetime,
    ) -> str:
        """Build human-readable reason for execution decision.

        Args:
            action: Signal action
            consecutive_days: Current consecutive days
            required_days: Required consecutive days
            should_execute: Whether to execute now
            will_persist: Whether signal will be persisted
            current_time: Current time for weekend detection

        Returns:
            Explanation string
        """
        if not will_persist:
            # Check if it's because of weekend duplicate or test run
            is_weekend = current_time.weekday() >= 5
            if is_weekend and current_time.time() >= self.market_close_time:
                return "⚠️ Weekend run - signal already exists for last trading day (Friday). Not persisted."
            return f"⚠️ Test run (before market close) - signal not persisted. Would need {required_days} consecutive days."

        if action == "HOLD":
            return "No action signal - continue holding."

        if should_execute:
            return f"✅ EXECUTE: {consecutive_days} consecutive {action} signals (required: {required_days})"

        remaining = required_days - consecutive_days
        return f"⏳ Wait: {consecutive_days}/{required_days} consecutive {action} signals ({remaining} more day{'s' if remaining > 1 else ''} needed)"

    def get_execution_summary(self) -> list[dict]:
        """Get summary of all securities ready for execution.

        Returns:
            List of securities with their execution status
        """
        summary = []

        for wkn, data in self.history.items():
            if not data["signals"]:
                continue

            latest_signal = data["signals"][-1]
            action = latest_signal["action"]

            if action == "HOLD":
                continue

            instrument_type = data.get("instrument_type", "warrant")
            required_days = self._get_required_days(action, instrument_type)
            consecutive_days = self._count_consecutive_signals(wkn, action)
            should_execute = consecutive_days >= required_days

            summary.append(
                {
                    "wkn": wkn,
                    "action": action,
                    "consecutive_days": consecutive_days,
                    "required_days": required_days,
                    "should_execute": should_execute,
                    "latest_date": latest_signal["date"],
                }
            )

        return summary

    def cleanup_old_signals(self, days_to_keep: int | None = None):
        """Remove signals older than specified days.

        Args:
            days_to_keep: Number of days of history to keep (default from settings)
        """
        if days_to_keep is None:
            days_to_keep = self.retention_days

        for wkn in self.history:
            signals = self.history[wkn]["signals"]
            if len(signals) > days_to_keep:
                self.history[wkn]["signals"] = signals[-days_to_keep:]

        self._save_history()
