"""
Warrant Screener
================

1. Reads ``mtf_underlyings`` (ISINs) from app/depots.py.
2. Fetches daily OHLCV history (NYSE/NASDAQ exchange prices) for every
   underlying.
3. Detects which underlyings are in a **stable uptrend** or have just
   **confirmed a new uptrend after a correction**.
4. For every qualifying underlying, queries ``GET /v1/warrants/`` for CALL
   warrants at-the-money (strike ±10 %, narrowed to ±5 % if >10 results)
   with 9–12 month maturity, fetches full analytics for up to
   MAX_DETAIL_FETCH candidates (1 per issuer, closest to ATM), scores them
   with the multi-criteria model, and picks the highest-scoring warrant.
5. Prints a ranked shortlist (passed hard-filters first, then filtered-out).

Usage
-----
    uv run python scripts/warrant_screener.py

API base URL
------------
    https://ca-fastapi.yellowwater-786ec0d0.germanywestcentral.azurecontainerapps.io

Notes
-----
- Container App scales to zero — allow up to 60 s for the cold start.
- History is fetched from the exchange (NYSE/NASDAQ) using
  ``id_notation=preferred_id_notation_exchange_trading`` so that prices are
  in USD — the same currency as warrant strike prices.
"""

import sys
import time
from datetime import date
from pathlib import Path

import httpx
import numpy as np
import pandas as pd
import talib

# Make app/ importable when run from the repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.depots import mtf_underlyings  # noqa: E402
from app.indicators import supertrend  # noqa: E402

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = "https://ca-fastapi.yellowwater-786ec0d0.germanywestcentral.azurecontainerapps.io"
WARMUP_TIMEOUT = 60.0  # cold-start may take up to 40-60 s
REQUEST_TIMEOUT = 30.0

# Scoring weights — must sum to 1.0
SCORING_WEIGHTS: dict[str, float] = {
    "delta": 0.30,
    "leverage": 0.20,
    "intrinsic_value": 0.15,
    "spread": 0.10,
    "premium_pa": 0.10,
    "remaining_time": 0.10,
    "implied_volatility": 0.05,
}

# Hard-filter constraints (warrants failing ANY of these are excluded)
HARD_FILTERS = {
    "min_remaining_days": 90,
    "max_leverage": 30.0,  # simple gearing (analytics.leverage)
    "max_spread_pct": 8.0,
    "min_score": 4.0,
}

# Maximum warrant candidates to fetch detail for per underlying.
# Candidates are pre-deduplicated to ≤1 per issuer (closest to ATM).
MAX_DETAIL_FETCH = 15

# Trend-detection parameters (daily candles, stock instrument)
_ST_ATR_PERIOD = 10  # Supertrend ATR period
_ST_MULTIPLIER = 3.0  # Supertrend band multiplier
_ADX_PERIOD = 14
_EMA_FAST_PERIOD = 5  # ~1 week
_EMA_SLOW_PERIOD = 13  # ~2.5 weeks
_ADX_MIN = 20  # minimum ADX to consider a trend "strong"
_FLIP_LOOKBACK = 30  # daily candles to look back for a recent ST flip


# ---------------------------------------------------------------------------
# Per-criterion scoring functions
# ---------------------------------------------------------------------------


def _score_delta(delta: float) -> float:
    if 0.5 <= delta <= 0.7:
        return 10.0
    if 0.4 <= delta < 0.5 or 0.7 < delta <= 0.8:
        return 7.0
    if 0.3 <= delta < 0.4:
        return 4.0
    return 0.0


def _score_leverage(leverage: float) -> float:
    """Uses the simple gearing ratio (analytics.leverage from API)."""
    if 4 <= leverage <= 10:
        return 10.0
    if 10 < leverage <= 15:
        return 7.0
    if 15 < leverage <= 25:
        return 4.0
    return 0.0


def _score_intrinsic(intrinsic: float) -> float:
    return 10.0 if intrinsic > 0 else 0.0


def _score_spread(spread_pct: float) -> float:
    if spread_pct < 2:
        return 10.0
    if spread_pct < 4:
        return 7.0
    if spread_pct < 6:
        return 4.0
    return 0.0


def _score_premium_pa(premium_pa: float) -> float:
    if premium_pa < 20:
        return 10.0
    if premium_pa < 30:
        return 7.0
    if premium_pa < 40:
        return 4.0
    return 0.0


def _score_remaining_time(days: int) -> float:
    if days > 270:  # > 9 months
        return 10.0
    if days > 180:  # 6–9 months
        return 7.0
    if days > 90:  # 3–6 months
        return 4.0
    return 0.0


def _score_iv(iv_pct: float) -> float:
    if iv_pct < 40:
        return 10.0
    if iv_pct < 60:
        return 7.0
    return 4.0  # > 60 %: still valid, just more expensive


# ---------------------------------------------------------------------------
# Warrant scoring
# ---------------------------------------------------------------------------


def compute_warrant_score(warrant_data: dict) -> dict:
    """
    Compute the multi-criteria warrant score.

    Returns a dict with:
        total_score          float  [0, 10]
        criteria             dict   per-criterion raw points
        passed_hard_filters  bool
        filter_reasons       list[str]
        remaining_days       int
        delta / leverage / intrinsic / spread_pct / premium_pa / iv  (raw values)
    """
    ref = warrant_data.get("reference_data", {})
    mkt = warrant_data.get("market_data", {})
    anly = warrant_data.get("analytics", {})

    # Remaining calendar days until maturity
    maturity_str = ref.get("maturity_date") or ref.get("last_trading_day")
    remaining_days = 0
    if maturity_str:
        try:
            maturity = date.fromisoformat(str(maturity_str))
            remaining_days = max(0, (maturity - date.today()).days)
        except ValueError:
            remaining_days = 0

    delta = float(anly.get("delta", 0) or 0)
    leverage = float(anly.get("leverage", 0) or 0)  # simple gearing
    intrinsic = float(anly.get("intrinsic_value", 0) or 0)
    spread_pct = float(mkt.get("spread_percent", 99) or 99)
    premium_pa = float(anly.get("premium_per_annum", 99) or 99)
    iv = float(anly.get("implied_volatility", 99) or 99)

    # --- Hard filters ---
    filter_reasons: list[str] = []
    if remaining_days < HARD_FILTERS["min_remaining_days"]:
        filter_reasons.append(f"expires in {remaining_days}d (<90d)")
    if leverage > HARD_FILTERS["max_leverage"]:
        filter_reasons.append(f"leverage={leverage:.1f}× (>30×)")
    if spread_pct > HARD_FILTERS["max_spread_pct"]:
        filter_reasons.append(f"spread={spread_pct:.1f}% (>8%)")

    # --- Per-criterion scores ---
    criteria = {
        "delta": _score_delta(delta),
        "leverage": _score_leverage(leverage),
        "intrinsic_value": _score_intrinsic(intrinsic),
        "spread": _score_spread(spread_pct),
        "premium_pa": _score_premium_pa(premium_pa),
        "remaining_time": _score_remaining_time(remaining_days),
        "implied_volatility": _score_iv(iv),
    }

    total_score = sum(SCORING_WEIGHTS[k] * criteria[k] for k in criteria)

    if total_score < HARD_FILTERS["min_score"]:
        filter_reasons.append(f"score={total_score:.2f} (<4.0)")

    return {
        "total_score": round(total_score, 2),
        "criteria": criteria,
        "passed_hard_filters": len(filter_reasons) == 0,
        "filter_reasons": filter_reasons,
        "remaining_days": remaining_days,
        # raw values for display
        "delta": delta,
        "leverage": leverage,
        "intrinsic": intrinsic,
        "spread_pct": spread_pct,
        "premium_pa": premium_pa,
        "iv": iv,
    }


# ---------------------------------------------------------------------------
# Trend detection
# ---------------------------------------------------------------------------


def detect_uptrend(df: pd.DataFrame) -> dict:
    """
    Classify the current trend for a daily OHLCV DataFrame.

    Returns
    -------
    dict with:
        is_uptrend   bool
        status       'stable' | 'new_confirmed' | 'weak' | 'bearish' | 'no_data'
        details      str  (human-readable summary)
    """
    close = df["close"].to_numpy(dtype=float)
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    n = len(close)

    min_candles = _EMA_SLOW_PERIOD + _ADX_PERIOD + 5
    if n < min_candles:
        return {
            "is_uptrend": False,
            "status": "no_data",
            "details": f"Only {n} candles (need ≥{min_candles})",
        }

    # --- Supertrend (returns numpy arrays) ---
    _, st_dir = supertrend(
        df["high"],
        df["low"],
        df["close"],
        atr_period=_ST_ATR_PERIOD,
        multiplier=_ST_MULTIPLIER,
    )
    st_current = st_dir[-1]  # +1 = bullish, -1 = bearish

    # --- EMAs ---
    ema_fast = talib.EMA(close, timeperiod=_EMA_FAST_PERIOD)
    ema_slow = talib.EMA(close, timeperiod=_EMA_SLOW_PERIOD)
    ema_bull = ema_fast[-1] > ema_slow[-1]

    # --- ADX + DI ---
    adx = talib.ADX(high, low, close, timeperiod=_ADX_PERIOD)
    plus_di = talib.PLUS_DI(high, low, close, timeperiod=_ADX_PERIOD)
    minus_di = talib.MINUS_DI(high, low, close, timeperiod=_ADX_PERIOD)
    adx_val = adx[-1]
    bull_di = plus_di[-1] > minus_di[-1]

    # --- Detect recent Supertrend flip (bearish → bullish) ---
    lookback = min(_FLIP_LOOKBACK, n - 1)
    recent_dir = st_dir[-(lookback + 1) :]  # numpy slice
    flipped_recently = False
    flip_candles_ago = None
    for i in range(1, len(recent_dir)):
        if recent_dir[i - 1] == -1 and recent_dir[i] == 1:
            flipped_recently = True
            flip_candles_ago = len(recent_dir) - 1 - i
            break

    # --- Rally from recent low (confirms re-entry after correction) ---
    recent_low = np.nanmin(low[-lookback:]) if lookback > 0 else low[-1]
    rally_pct = ((close[-1] - recent_low) / recent_low) * 100 if recent_low > 0 else 0.0

    adx_info = f"ADX={adx_val:.1f}"
    di_info = f"+DI={plus_di[-1]:.1f} {'>' if bull_di else '<'} -DI={minus_di[-1]:.1f}"
    ema_info = f"EMA{_EMA_FAST_PERIOD}({'>' if ema_bull else '<'})EMA{_EMA_SLOW_PERIOD}"

    if st_current == 1 and ema_bull and adx_val >= _ADX_MIN and bull_di:
        if flipped_recently:
            status = "new_confirmed"
            details = (
                f"New uptrend confirmed {flip_candles_ago}d ago — "
                f"{adx_info}, {di_info}, {ema_info}, "
                f"rally={rally_pct:.1f}% from {lookback}d low"
            )
        else:
            status = "stable"
            details = f"Stable uptrend — {adx_info}, {di_info}, {ema_info}, ST bullish"
        return {"is_uptrend": True, "status": status, "details": details}

    elif st_current == 1 and adx_val >= _ADX_MIN:
        # ST bullish + trend strength, but EMA or DI not fully aligned
        details = f"Weak/mixed — ST bullish but EMA not confirmed, {adx_info}, {di_info}"
        return {"is_uptrend": False, "status": "weak", "details": details}

    else:
        details = (
            f"Bearish/ranging — ST={'bull' if st_current == 1 else 'bear'}, {adx_info}, {ema_info}"
        )
        return {"is_uptrend": False, "status": "bearish", "details": details}


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------


def _wake_up_api(client: httpx.Client) -> bool:
    print("⏳ Waking up API (cold-start may take up to 60 s)...", flush=True)
    for attempt in range(4):
        try:
            r = client.get(f"{BASE_URL}/", timeout=WARMUP_TIMEOUT)
            if r.status_code == 200:
                print("✅ API is live.\n")
                return True
            print(f"   Attempt {attempt + 1}: HTTP {r.status_code} — retrying…")
        except httpx.RequestError as exc:
            print(f"   Attempt {attempt + 1}: {exc} — retrying…")
        time.sleep(5)
    return False


def _fetch_history(identifier: str, client: httpx.Client) -> tuple[str, pd.DataFrame] | None:
    # Request 6 months of daily data — enough for all indicator warm-up periods
    from datetime import timedelta

    start_dt = (date.today() - timedelta(days=183)).strftime("%Y-%m-%dT00:00:00")
    try:
        r = client.get(
            f"{BASE_URL}/v1/history/{identifier}",
            params={"interval": "day", "start": start_dt},
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        name = data.get("name") or identifier
        rows = data.get("data", [])
        if not rows:
            return None
        df = pd.DataFrame(rows)
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df.sort_values("datetime").reset_index(drop=True)
        return str(name), df
    except Exception as exc:
        print(f"   ❌ History fetch failed for {identifier}: {exc}")
        return None


def _fetch_warrant(wkn: str, client: httpx.Client) -> dict | None:
    try:
        r = client.get(
            f"{BASE_URL}/v1/warrants/{wkn}",
            params={"id_notation": "preferred_id_notation_life_trading"},
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        print(f"   ❌ Warrant fetch failed for {wkn}: {exc}")
        return None


def _fetch_warrant_candidates(
    isin: str,
    current_price: float,
    client: httpx.Client,
) -> list[dict]:
    """Search for at-the-money CALL warrants with 9–12 month maturity.

    Tries ±10 % strike range first; if more than 10 results are returned,
    narrows to ±5 %.  Returns a deduplicated shortlist of at most
    MAX_DETAIL_FETCH candidates (one per issuer, with the strike closest
    to the current price).
    """
    from datetime import timedelta

    maturity_from = (date.today() + timedelta(days=273)).strftime("%Y-%m-%d")  # ~9 months
    maturity_to = (date.today() + timedelta(days=365)).strftime("%Y-%m-%d")  # ~12 months

    candidates: list[dict] = []
    for pct in [0.10, 0.05]:
        strike_min = round(current_price * (1 - pct), 2)
        strike_max = round(current_price * (1 + pct), 2)
        try:
            r = client.get(
                f"{BASE_URL}/v1/warrants/",
                params={
                    "underlying": isin,
                    "preselection": "CALL",
                    "strike_min": strike_min,
                    "strike_max": strike_max,
                    "maturity_from": maturity_from,
                    "maturity_to": maturity_to,
                    "issuer_action": "TRUE",
                    "issuer_no_fee_action": "TRUE",
                },
                timeout=REQUEST_TIMEOUT,
            )
            r.raise_for_status()
            data = r.json()
            candidates = data.get("results") or []
            count = data.get("count", len(candidates))
            print(
                f"     finder ±{int(pct * 100)}%  "
                f"strike=[{strike_min:.1f}–{strike_max:.1f}]  "
                f"maturity={maturity_from}–{maturity_to}  "
                f"→ {count} candidate(s)",
                flush=True,
            )
            if count <= 10:
                break  # narrow range not needed
        except Exception as exc:
            print(f"   ❌ Warrant finder failed (±{int(pct * 100)}%): {exc}")
            candidates = []

    if not candidates:
        return []

    # De-duplicate: keep the strike closest to current price per issuer
    by_issuer: dict[str, dict] = {}
    for c in candidates:
        issuer = c.get("issuer") or "unknown"
        strike = float(c.get("strike") or 0)
        prev = by_issuer.get(issuer)
        if prev is None or abs(strike - current_price) < abs(
            float(prev.get("strike") or 0) - current_price
        ):
            by_issuer[issuer] = c

    # Sort by ATM-ness and cap
    shortlist = sorted(
        by_issuer.values(),
        key=lambda c: abs(float(c.get("strike") or 0) - current_price),
    )
    return shortlist[:MAX_DETAIL_FETCH]


# ---------------------------------------------------------------------------
# Rating label
# ---------------------------------------------------------------------------


def _rating(score: float) -> str:
    if score >= 8:
        return "Excellent"
    if score >= 6:
        return "Good"
    if score >= 4:
        return "Mediocre"
    return "Unsuitable"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    sep = "═" * 80
    sep2 = "─" * 80

    print(f"\n{sep}")
    print(f"  WARRANT SCREENER  ·  {date.today()}")
    print(f"{sep}\n")
    print(f"  Scanning {len(mtf_underlyings)} underlyings from mtf_underlyings …\n")

    uptrend_stocks: list[dict] = []

    with httpx.Client() as client:
        # ── 1. Wake up container ────────────────────────────────────────────
        if not _wake_up_api(client):
            print("❌ API failed to wake up. Aborting.")
            sys.exit(1)

        # ── 2. Fetch OHLCV + trend analysis ─────────────────────────────────
        print(f"  {'UNDERLYING':<32}  {'Price':>8}  {'STATUS':<16}  DETAILS")
        print(sep2)

        for isin in mtf_underlyings:
            result = _fetch_history(isin, client)
            if result is None:
                print(f"  {'(fetch error)':<32}  {'—':>8}  {'—':<16}  {isin}")
                continue

            name, df = result
            trend = detect_uptrend(df)
            current_price = float(df["close"].iloc[-1])

            if trend["is_uptrend"]:
                icon = "✅"
                label = "UPTREND"
            elif trend["status"] == "weak":
                icon = "⚠️ "
                label = "WEAK"
            else:
                icon = "🔻"
                label = "BEARISH"

            short_name = name[:30]
            print(
                f"  {icon} {short_name:<30}  {current_price:>8.2f}  {label:<16}  {trend['details']}"
            )

            if trend["is_uptrend"]:
                uptrend_stocks.append(
                    {
                        "isin": isin,
                        "name": name,
                        "trend": trend,
                        "current_price": current_price,
                    }
                )

        print(sep2)
        print(
            f"\n  → {len(uptrend_stocks)} in uptrend, "
            f"{len(mtf_underlyings) - len(uptrend_stocks)} bearish/weak/no-data\n"
        )

        if not uptrend_stocks:
            print("  No stocks in uptrend detected — no warrant scoring performed.")
            return

        # ── 3. Search, score, and pick best warrant per underlying ───────────
        print(f"{sep}")
        print("  WARRANT CANDIDATE SEARCH + SCORING")
        print(f"{sep}\n")

        scored: list[dict] = []

        for stock in uptrend_stocks:
            isin = stock["isin"]
            name = stock["name"]
            current_price = stock["current_price"]

            print(f"  ▶ {name[:46]}  (current price: {current_price:.2f})")

            candidates = _fetch_warrant_candidates(isin, current_price, client)
            if not candidates:
                print("     ⚠️  No candidates found — skipped\n")
                continue

            print(f"     Scoring {len(candidates)} candidate(s)…")

            best: dict | None = None
            best_score: float = -1.0

            for cand in candidates:
                wkn = cand.get("wkn") or cand.get("isin", "")
                warrant_data = _fetch_warrant(wkn, client)
                if warrant_data is None:
                    continue

                score_result = compute_warrant_score(warrant_data)
                issuer = (cand.get("issuer") or "")[:18]
                cand_strike = cand.get("strike", "?")
                print(
                    f"       {wkn:<8}  {issuer:<18}  strike={cand_strike:<8}"
                    f"  score={score_result['total_score']:.2f}"
                    f"  {'✅' if score_result['passed_hard_filters'] else '❌'}"
                )

                if score_result["total_score"] > best_score:
                    best_score = score_result["total_score"]
                    best = {
                        "name": name,
                        "underlying_isin": isin,
                        "current_price": current_price,
                        "warrant_wkn": wkn,
                        "warrant_isin": warrant_data.get("isin", ""),
                        "trend_status": stock["trend"]["status"],
                        "trend_details": stock["trend"]["details"],
                        "score": score_result,
                        "ref": warrant_data.get("reference_data", {}),
                        "mkt": warrant_data.get("market_data", {}),
                        "anly": warrant_data.get("analytics", {}),
                        "finder_issuer": cand.get("issuer", ""),
                    }

            if best is not None:
                status_icon = "✅" if best["score"]["passed_hard_filters"] else "❌"
                print(
                    f"     → best: {best['warrant_wkn']}  "
                    f"score={best['score']['total_score']:.2f}  "
                    f"{status_icon} {_rating(best['score']['total_score'])}\n"
                )
                scored.append(best)
            else:
                print("     ⚠️  No scoreable warrant detail retrieved\n")

        if not scored:
            print("\n  No warrant data could be retrieved.")
            return

    # ── 4. Sort: passed hard filters first, then by score desc ──────────────
    passed = sorted(
        [s for s in scored if s["score"]["passed_hard_filters"]],
        key=lambda x: x["score"]["total_score"],
        reverse=True,
    )
    failed = sorted(
        [s for s in scored if not s["score"]["passed_hard_filters"]],
        key=lambda x: x["score"]["total_score"],
        reverse=True,
    )
    ranked = passed + failed

    # ── 5. Print ranked table ────────────────────────────────────────────────
    W = 116
    print(f"\n\n{'═' * W}")
    print("  RANKED WARRANT SHORTLIST  (best warrant per uptrending underlying)")
    print(f"{'═' * W}")
    print(
        f"  {'#':<3}  {'Underlying':<26}  {'WKN':<10}  {'Issuer':<16}  {'Trend':<15}"
        f"  {'Score':>6}  {'Rating':<11}"
        f"  {'δ':>5}  {'Lev':>6}  {'IV%':>5}  {'Spr%':>5}  {'Prem%pa':>7}"
        f"  {'Days':>5}  {'Ask':>7}  {'Strike':>8}"
    )
    print("─" * W)

    for rank, s in enumerate(ranked, 1):
        sc = s["score"]
        ref = s["ref"]
        mkt = s["mkt"]
        passed_mark = "✅" if sc["passed_hard_filters"] else "❌"
        trend_label = {
            "stable": "Stable ↑",
            "new_confirmed": "New ↑ (conf.)",
        }.get(s["trend_status"], s["trend_status"])

        ask_price = mkt.get("ask") or mkt.get("bid") or 0.0
        strike = ref.get("strike", 0.0) or 0.0
        issuer = (s.get("finder_issuer") or ref.get("issuer") or "")[:16]

        print(
            f"  {rank:<3}  {s['name'][:26]:<26}  "
            f"{passed_mark}{s['warrant_wkn']:<9}  "
            f"{issuer:<16}  "
            f"{trend_label:<15}"
            f"  {sc['total_score']:>6.2f}  {_rating(sc['total_score']):<11}"
            f"  {sc['delta']:>5.2f}  {sc['leverage']:>6.1f}  "
            f"{sc['iv']:>5.1f}  {sc['spread_pct']:>5.2f}  "
            f"{sc['premium_pa']:>7.1f}  {sc['remaining_days']:>5}  "
            f"{ask_price:>7.3f}  {strike:>8.2f}"
        )
        if not sc["passed_hard_filters"]:
            print(f"       ↳ Filtered: {', '.join(sc['filter_reasons'])}")

    print("═" * W)
    print(
        f"\n  {len(passed)} warrant(s) passed all hard filters  ·  "
        f"{len(failed)} filtered out  ·  "
        f"{len(mtf_underlyings) - len(uptrend_stocks)} underlying(s) not in uptrend\n"
    )

    # ── 6. Detailed breakdown for top 3 ─────────────────────────────────────
    if passed:
        print(f"{'─' * W}")
        print("  CRITERION BREAKDOWN — top 3 passing warrants")
        print(f"{'─' * W}")
        for s in passed[:3]:
            sc = s["score"]
            print(
                f"\n  {s['name']}  ({s['warrant_wkn']})  —  "
                f"{_rating(sc['total_score'])}  [{sc['total_score']:.2f}/10]"
            )
            print(f"  Trend:  {s['trend_details']}")
            print(
                f"  Price:  {s['current_price']:.2f}  "
                f"Strike: {s['ref'].get('strike', '?')}  "
                f"Issuer: {s.get('finder_issuer', '')}\n"
            )
            header = f"  {'Criterion':<22}  {'Points':>6}  {'Weight':>7}  {'Contrib':>8}"
            print(header)
            print("  " + "─" * (len(header) - 2))
            for crit, pts in sc["criteria"].items():
                wt = SCORING_WEIGHTS[crit]
                contrib = wt * pts
                print(f"  {crit:<22}  {pts:>6.1f}  {wt:>6.0%}  {contrib:>8.3f}")
            print(f"  {'TOTAL':<22}  {'':>6}  {'':>7}  {sc['total_score']:>8.2f}")

    print()


if __name__ == "__main__":
    main()
