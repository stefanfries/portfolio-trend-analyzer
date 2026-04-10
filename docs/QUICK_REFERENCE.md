# Signal Confirmation - Quick Reference

## TL;DR

- ✅ Signals only persist after 22:00 (market close)
- ✅ Weekend runs use Friday's date (no duplicates)
- ✅ Warrants: Execute after 2 consecutive days
- ✅ Stocks: Execute after 3 consecutive days  
- ✅ STRONG_SELL: Execute after 1 day
- ✅ Test runs (before 22:00) don't pollute history

## Usage

### Production (After Market Close)

```bash
uv run python -m app.main
```

### Testing (Any Time)

```bash
uv run python -m app.main
# Shows signals but doesn't save them
```

### Force Save (Override)

```bash
uv run python -m app.main --force-save
# Saves signals even before 22:00
```

## What You'll See

### Before Market Close (Test Run)

```text
⚙️ Test run (before market close) - signals will NOT be persisted
   Use --force-save to persist signals during market hours
```

### After Market Close (Official Run)

```text
🕒 Running after market close (22:00) - signals will be persisted
```

### Weekend Run

```text
🕒 Running after market close on weekend
   Signals will use Friday's trading day to avoid duplicates
```

If Friday's signal already exists:

```text
📋 Execution: ⚠️ Weekend run - signal already exists for last trading day (Friday). Not persisted.
```

### Execution Recommendations

```text
📋 Execution: ✅ EXECUTE: 2 consecutive BUY signals (required: 2)
📋 Execution: ⏳ Wait: 1/2 consecutive BUY signals (1 more day needed)
```

### Summary at End

```text
🎯 READY TO EXECUTE (2 securities):
  • MM3GS6: BUY (2 consecutive days)
  • SJ7957: SELL (2 consecutive days)
```

## Files Created

- `app/signal_history.py` - Core tracking logic
- `results/signal_history.json` - Signal history data
- `tests/test_signal_history.py` - Test suite
- `docs/SIGNAL_CONFIRMATION.md` - Full documentation

## Example Workflow

**Day 1 (Monday 22:30)**

```bash
uv run python -m app.main
# Output: ⏳ Wait: 1/2 consecutive BUY signals for MM3GS6
```

**Day 2 (Tuesday 22:30)**

```bash
uv run python -m app.main
# Output: ✅ EXECUTE: 2 consecutive BUY signals for MM3GS6
```

**Wednesday Morning**

- Execute the BUY order for MM3GS6

## Configuration

Settings are configured in `.env`:

```env
# Market close time (default: 22:00)
SIGNAL_HISTORY_MARKET_CLOSE_HOUR=22
SIGNAL_HISTORY_MARKET_CLOSE_MINUTE=0

# History retention (default: 30 days)
SIGNAL_HISTORY_RETENTION_DAYS=30
```

Confirmation rules: Editable in `signal_history.py`
