# Signal Confirmation Tracking

This feature implements a consecutive signal confirmation system to reduce false trading signals and improve execution timing.

## Overview

Instead of acting on every signal immediately, the system now tracks signals across multiple days and only recommends execution after **consecutive confirmation**:

- **Warrants**: 2 consecutive days (except STRONG_SELL)
- **Stocks**: 3 consecutive days (except STRONG_SELL)
- **STRONG_SELL**: Immediate execution after 1 day (capital protection)

## How It Works

### 1. Daily Analysis

Run your analysis after market close (22:00):

```bash
uv run python -m app.main
```

### 2. Signal Persistence

- **After 22:00**: Signals are automatically persisted to `results/signal_history.json`
- **Before 22:00**: Test runs do NOT persist signals (prevents pollution during development)

### 3. Consecutive Tracking

Example for a warrant:

| Day | Signal | Consecutive Days | Action |
| --- | ------ | ---------------- | ------ |
| Mon | BUY | 1 | Wait (need 2 days) |
| Tue | BUY | 2 | ✅ **EXECUTE** |

If the signal changes:

| Day | Signal | Consecutive Days | Action |
| --- | ------ | -----------------| ------ |
| Mon | BUY | 1 | Wait |
| Tue | HOLD | 0 | Wait (reset counter) |
| Wed | BUY | 1 | Wait (starting over) |

### 4. Execution Recommendations

The system shows clear execution status:

```text
📋 Execution: ✅ EXECUTE: 2 consecutive BUY signals (required: 2)
📋 Execution: ⏳ Wait: 1/2 consecutive BUY signals (1 more day needed)
```

## Command Line Options

### Normal Run (After Market Close)

```bash
uv run python -m app.main
```

- Only persists signals if run after 22:00
- Recommended for production use

### Force Save (Override Market Hours)

```bash
uv run python -m app.main --force-save
```

- Persists signals regardless of time
- Use for manual override or specific testing scenarios

### Test Mode (Before Market Close)

```bash
# Run at 3 PM (15:00)
uv run python -m app.main
```

- Shows what signals would be, but doesn't persist them
- Perfect for development and testing
- Output shows: ⚙️ Test run (before market close) - signals will NOT be persisted

## Signal History File

Location: `results/signal_history.json`

Example structure:

```json
{
  "MM3GS6": {
    "signals": [
      {
        "date": "2026-02-24",
        "action": "BUY",
        "confidence": "HIGH"
      },
      {
        "date": "2026-02-25",
        "action": "BUY",
        "confidence": "HIGH"
      }
    ],
    "instrument_type": "warrant"
  }
}
```

### Automatic Cleanup

- Keeps last 30 days per security
- Automatically removes older signals

## Excel Reports

The Excel reports now include an "Execution Status" column:

- `✅ EXECUTE NOW` - Action ready to be taken
- `⏳ 1/2 days` - Waiting for confirmation
- `⏳ 2/3 days` - Waiting for confirmation

## Execution Summary

After each run, you'll see a summary:

```text
================================================================================
🎯 READY TO EXECUTE (2 securities):
================================================================================
  • MM3GS6: BUY (2 consecutive days)
  • SJ7957: SELL (2 consecutive days)
================================================================================
```

Or tracking status during test runs:

```text
================================================================================
📊 SIGNAL TRACKING STATUS:
================================================================================
  ✅ READY MM3GS6: BUY (2/2 days)
  ⏳ WAITING JK9V0Y: SELL (1/2 days)
  ⏳ WAITING SY026G: BUY (1/3 days)
================================================================================
```

## Benefits

### 1. Reduced False Signals

- Filters out single-day noise
- Requires trend confirmation
- Multi-indicator validation (already in place) + time confirmation

### 2. Lower Transaction Costs

- Fewer trades = less fees
- Better entry/exit timing
- Reduced emotional trading

### 3. Capital Protection

- STRONG_SELL still executes quickly (1 day)
- Genuine trends persist for multiple days
- Avoid whipsaw losses

### 4. Better Risk Management

- More time to evaluate position
- Clearer conviction before execution
- Historical tracking for performance analysis

## Configuration

All signal history settings are configured via the `.env` file using Pydantic settings.

### Market Close Time

Default: 22:00 (10 PM)

Configure in `.env`:

```env
SIGNAL_HISTORY_MARKET_CLOSE_HOUR=22
SIGNAL_HISTORY_MARKET_CLOSE_MINUTE=0
```

### Signal Retention Period

Default: 30 days

Configure in `.env`:

```env
SIGNAL_HISTORY_RETENTION_DAYS=30
```

### Required Consecutive Days

To modify confirmation periods, edit `_get_required_days()` in `app/signal_history.py`:

```python
def _get_required_days(self, action: SignalAction, instrument_type: InstrumentType) -> int:
    if action == "STRONG_SELL":
        return 1
    
    if instrument_type == "warrant":
        return 2  # Change to 3 for even more confirmation
    
    return 3  # Change to 2 for faster stock execution
```

## Testing

Run the test suite:

```bash
uv run python -m tests.test_signal_history
```

Tests cover:

- Market close detection
- Consecutive signal tracking
- Signal change/reset
- STRONG_SELL immediate execution
- Stock vs warrant confirmation periods
- Force-save functionality

## Workflow Recommendations

### Daily Routine (Recommended)

1. **22:00+**: Run analysis after market close

   ```bash
   uv run python -m app.main
   ```

2. **Review**: Check execution summary

3. **Next Day**: Execute recommended trades during market hours

4. **Track**: Monitor positions and outcomes

### Development/Testing

1. **Anytime**: Run without persistence

   ```bash
   uv run python -m app.main
   # Signals shown but not saved
   ```

2. **Override if needed**: Use force-save

   ```bash
   uv run python -m app.main --force-save
   # Signals saved despite market hours
   ```

## Troubleshooting

### Signals Not Persisting

- Check if running after 22:00
- Use `--force-save` to override
- Verify `results/` directory is writable

### Counter Not Incrementing

- Ensure same signal appears consecutively
- Check signal_history.json for actual data
- Verify dates are sequential (no gaps)

### Wrong Instrument Type

- Set `INSTRUMENT_TYPE` correctly in main.py
- "stock" vs "warrant" affects required days
- History updates on each run

## Future Enhancements

Potential additions:

- SQLite backend for historical analysis
- Backtesting framework using signal history
- Email notifications on execution recommendations
- Web dashboard for signal visualization
- Performance metrics (win rate, avg return per confirmed signal)
