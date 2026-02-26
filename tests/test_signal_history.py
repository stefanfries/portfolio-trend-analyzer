"""Tests for signal history tracking functionality."""

import tempfile
from datetime import datetime
from pathlib import Path

from app.signal_history import SignalHistoryManager


def test_signal_tracking_before_market_close():
    """Test that signals are not persisted before market close."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "test_history.json"
        manager = SignalHistoryManager(history_file=history_file)

        # Simulate test run at 15:00 (3 PM - before market close)
        test_time = datetime(2026, 2, 26, 15, 0, 0)

        rec = manager.add_signal(
            wkn="TEST123",
            action="BUY",
            confidence="HIGH",
            instrument_type="warrant",
            force_save=False,
            current_time=test_time,
        )

        # Should not persist
        assert rec["will_persist"] is False
        assert rec["should_execute"] is False
        assert "Test run" in rec["reason"]

        # File should not exist or be empty
        if history_file.exists():
            import json

            with open(history_file) as f:
                data = json.load(f)
            assert "TEST123" not in data or len(data["TEST123"]["signals"]) == 0


def test_signal_tracking_after_market_close():
    """Test that signals are persisted after market close."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "test_history.json"
        manager = SignalHistoryManager(history_file=history_file)

        # Simulate run at 22:30 (10:30 PM - after market close)
        test_time = datetime(2026, 2, 26, 22, 30, 0)

        rec = manager.add_signal(
            wkn="TEST123",
            action="BUY",
            confidence="HIGH",
            instrument_type="warrant",
            force_save=False,
            current_time=test_time,
        )

        # Should persist
        assert rec["will_persist"] is True
        assert rec["consecutive_days"] == 1
        assert rec["required_days"] == 2  # Warrants need 2 days

        # File should exist and contain signal
        assert history_file.exists()
        import json

        with open(history_file) as f:
            data = json.load(f)
        assert "TEST123" in data
        assert len(data["TEST123"]["signals"]) == 1


def test_consecutive_signal_tracking():
    """Test consecutive signal counting for execution decision."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "test_history.json"
        manager = SignalHistoryManager(history_file=history_file)

        # Day 1: First BUY signal
        day1 = datetime(2026, 2, 24, 22, 30, 0)
        rec1 = manager.add_signal(
            wkn="TEST123",
            action="BUY",
            confidence="HIGH",
            instrument_type="warrant",
            force_save=False,
            current_time=day1,
        )
        assert rec1["consecutive_days"] == 1
        assert rec1["should_execute"] is False

        # Day 2: Second consecutive BUY signal
        day2 = datetime(2026, 2, 25, 22, 30, 0)
        rec2 = manager.add_signal(
            wkn="TEST123",
            action="BUY",
            confidence="HIGH",
            instrument_type="warrant",
            force_save=False,
            current_time=day2,
        )
        assert rec2["consecutive_days"] == 2
        assert rec2["should_execute"] is True  # 2 consecutive days for warrants
        assert "EXECUTE" in rec2["reason"]


def test_signal_change_resets_counter():
    """Test that changing signal resets consecutive counter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "test_history.json"
        manager = SignalHistoryManager(history_file=history_file)

        # Day 1: BUY signal
        day1 = datetime(2026, 2, 24, 22, 30, 0)
        manager.add_signal(
            wkn="TEST123",
            action="BUY",
            confidence="HIGH",
            instrument_type="warrant",
            current_time=day1,
        )

        # Day 2: HOLD signal (change)
        day2 = datetime(2026, 2, 25, 22, 30, 0)
        manager.add_signal(
            wkn="TEST123",
            action="HOLD",
            confidence="MEDIUM",
            instrument_type="warrant",
            current_time=day2,
        )

        # Day 3: BUY signal again (should be back to 1 consecutive)
        day3 = datetime(2026, 2, 26, 22, 30, 0)
        rec = manager.add_signal(
            wkn="TEST123",
            action="BUY",
            confidence="HIGH",
            instrument_type="warrant",
            current_time=day3,
        )

        assert rec["consecutive_days"] == 1
        assert rec["should_execute"] is False


def test_strong_sell_immediate_execution():
    """Test that STRONG_SELL signals execute after just 1 day."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "test_history.json"
        manager = SignalHistoryManager(history_file=history_file)

        # Day 1: STRONG_SELL signal
        day1 = datetime(2026, 2, 26, 22, 30, 0)
        rec = manager.add_signal(
            wkn="TEST123",
            action="STRONG_SELL",
            confidence="HIGH",
            instrument_type="warrant",
            current_time=day1,
        )

        assert rec["consecutive_days"] == 1
        assert rec["required_days"] == 1
        assert rec["should_execute"] is True  # Immediate execution


def test_stock_requires_more_days():
    """Test that stocks require 3 consecutive days."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "test_history.json"
        manager = SignalHistoryManager(history_file=history_file)

        # Add 2 consecutive BUY signals for a stock
        day1 = datetime(2026, 2, 24, 22, 30, 0)
        manager.add_signal(
            wkn="STOCK001",
            action="BUY",
            confidence="HIGH",
            instrument_type="stock",
            current_time=day1,
        )

        day2 = datetime(2026, 2, 25, 22, 30, 0)
        rec2 = manager.add_signal(
            wkn="STOCK001",
            action="BUY",
            confidence="HIGH",
            instrument_type="stock",
            current_time=day2,
        )

        # Should not execute after 2 days (stocks need 3)
        assert rec2["consecutive_days"] == 2
        assert rec2["required_days"] == 3
        assert rec2["should_execute"] is False

        # Day 3: Should now execute
        day3 = datetime(2026, 2, 26, 22, 30, 0)
        rec3 = manager.add_signal(
            wkn="STOCK001",
            action="BUY",
            confidence="HIGH",
            instrument_type="stock",
            current_time=day3,
        )
        assert rec3["consecutive_days"] == 3
        assert rec3["should_execute"] is True


def test_force_save_flag():
    """Test that force_save overrides market close check."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "test_history.json"
        manager = SignalHistoryManager(history_file=history_file)

        # Simulate test run at 15:00 (before market close) with force_save
        test_time = datetime(2026, 2, 26, 15, 0, 0)

        rec = manager.add_signal(
            wkn="TEST123",
            action="BUY",
            confidence="HIGH",
            instrument_type="warrant",
            force_save=True,  # Force save despite market hours
            current_time=test_time,
        )

        # Should persist despite being before market close
        assert rec["will_persist"] is True

        # File should exist
        assert history_file.exists()


def test_weekend_duplicate_prevention():
    """Test that signals are not duplicated when run on weekends."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "test_history.json"
        manager = SignalHistoryManager(history_file=history_file)

        # Friday 22:30: First signal
        friday = datetime(2026, 2, 27, 22, 30, 0)  # Friday
        rec_friday = manager.add_signal(
            wkn="TEST123",
            action="BUY",
            confidence="HIGH",
            instrument_type="warrant",
            force_save=False,
            current_time=friday,
        )
        assert rec_friday["will_persist"] is True
        assert len(manager.history["TEST123"]["signals"]) == 1
        assert manager.history["TEST123"]["signals"][0]["date"] == "2026-02-27"

        # Saturday 22:30: Should not add duplicate signal
        saturday = datetime(2026, 2, 28, 22, 30, 0)  # Saturday
        rec_saturday = manager.add_signal(
            wkn="TEST123",
            action="BUY",
            confidence="HIGH",
            instrument_type="warrant",
            force_save=False,
            current_time=saturday,
        )
        # Should not persist (duplicate for Friday)
        assert rec_saturday["will_persist"] is False
        # Should still only have 1 signal (from Friday)
        assert len(manager.history["TEST123"]["signals"]) == 1
        assert "Weekend run" in rec_saturday["reason"]

        # Sunday 22:30: Should also not add duplicate
        sunday = datetime(2026, 3, 1, 22, 30, 0)  # Sunday
        rec_sunday = manager.add_signal(
            wkn="TEST123",
            action="BUY",
            confidence="HIGH",
            instrument_type="warrant",
            force_save=False,
            current_time=sunday,
        )
        assert rec_sunday["will_persist"] is False
        assert len(manager.history["TEST123"]["signals"]) == 1


def test_weekend_uses_friday_date():
    """Test that weekend signals use Friday's date for trading day."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "test_history.json"
        manager = SignalHistoryManager(history_file=history_file)

        # Saturday - should map to Friday's date
        saturday = datetime(2026, 2, 28, 22, 30, 0)  # Saturday
        trading_day = manager._get_current_trading_day(saturday)
        assert trading_day == "2026-02-27"  # Friday

        # Sunday - should also map to Friday's date
        sunday = datetime(2026, 3, 1, 22, 30, 0)  # Sunday
        trading_day = manager._get_current_trading_day(sunday)
        assert trading_day == "2026-02-27"  # Friday

        # Monday - should use Monday's date
        monday = datetime(2026, 3, 2, 22, 30, 0)  # Monday
        trading_day = manager._get_current_trading_day(monday)
        assert trading_day == "2026-03-02"  # Monday


if __name__ == "__main__":
    # Run tests manually
    test_signal_tracking_before_market_close()
    print("✅ Test 1 passed: Signals not persisted before market close")

    test_signal_tracking_after_market_close()
    print("✅ Test 2 passed: Signals persisted after market close")

    test_consecutive_signal_tracking()
    print("✅ Test 3 passed: Consecutive signal tracking works")

    test_signal_change_resets_counter()
    print("✅ Test 4 passed: Signal change resets counter")

    test_strong_sell_immediate_execution()
    print("✅ Test 5 passed: STRONG_SELL executes immediately")

    test_stock_requires_more_days()
    print("✅ Test 6 passed: Stocks require 3 consecutive days")

    test_force_save_flag()
    print("✅ Test 7 passed: Force save flag works")

    test_weekend_duplicate_prevention()
    print("✅ Test 8 passed: Weekend duplicate prevention works")

    test_weekend_uses_friday_date()
    print("✅ Test 9 passed: Weekend uses Friday trading day")

    print("\n🎉 All tests passed!")
