"""Compare portfolio analysis results between runs."""

from datetime import datetime, timedelta
from pathlib import Path

# Depot changes
REMOVED_TODAY = {
    "JU5YHH": "Qualcomm Inc.",
    "JU3YAP": "Nasdaq Inc.",
    "HT5D3H": "Walmart Inc.",
    "JK9Z20": "Microsoft Corporation",
}

ADDED_TODAY = {
    "MJ5417": "Regeneron Pharmaceuticals Inc.",
    "PK64FA": "KLA Corp.",
}

COMMON_SECURITIES = [
    ("HT8UZB", "Alphabet Inc."),
    ("HS4P7G", "Amazon.com Inc."),
    ("JT2GHE", "Meta Platforms Inc."),
    ("JH4WD6", "Apple Inc."),
    ("HS765P", "Starbucks Corporation"),
    ("MK74CT", "GE Aerospace & Defense"),
    ("MM2DRR", "EssilorLuxottica S.A."),
    ("MG9VYR", "Cisco Systems Inc."),
    ("JK9V0Y", "Nvidia Corporation"),
    ("MM5J03", "Newmont Corporation"),
    ("JH5VLN", "Blackrock Inc."),
    ("HT93ZB", "Allianz SE"),
    ("MM0CVV", "Applied Materials Inc."),
]


def analyze_chart_availability():
    """Analyze which charts exist for yesterday and today."""
    charts_dir = Path("charts")
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    print("=" * 80)
    print("DEPOT COMPOSITION CHANGES")
    print("=" * 80)
    print(f"\n📅 Comparing: {yesterday} vs {today}\n")

    print("❌ REMOVED FROM DEPOT (4 securities):")
    for wkn, name in REMOVED_TODAY.items():
        chart_yesterday = charts_dir / f"candlestick_{wkn}_{yesterday}.png"
        status = "✓" if chart_yesterday.exists() else "✗"
        print(f"  [{status}] {wkn} - {name}")

    print("\n✅ ADDED TO DEPOT (2 securities):")
    for wkn, name in ADDED_TODAY.items():
        chart_today = charts_dir / f"candlestick_{wkn}_{today}.png"
        status = "✓" if chart_today.exists() else "✗"
        print(f"  [{status}] {wkn} - {name}")

    print("\n🔄 COMMON SECURITIES (13 securities):")
    both_exist = []
    yesterday_only = []
    today_only = []
    neither = []

    for wkn, name in COMMON_SECURITIES:
        chart_yesterday = charts_dir / f"candlestick_{wkn}_{yesterday}.png"
        chart_today = charts_dir / f"candlestick_{wkn}_{today}.png"

        has_yesterday = chart_yesterday.exists()
        has_today = chart_today.exists()

        status = ""
        if has_yesterday and has_today:
            status = "✓✓"
            both_exist.append((wkn, name))
        elif has_yesterday and not has_today:
            status = "✓✗"
            yesterday_only.append((wkn, name))
        elif not has_yesterday and has_today:
            status = "✗✓"
            today_only.append((wkn, name))
        else:
            status = "✗✗"
            neither.append((wkn, name))

        print(f"  [{status}] {wkn} - {name}")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"  Comparable (both dates): {len(both_exist)}")
    print(f"  Only yesterday: {len(yesterday_only)}")
    print(f"  Only today (running): {len(today_only)}")
    print(f"  Neither date: {len(neither)}")

    print("\n" + "=" * 80)
    print("DEPOT SIZE")
    print("=" * 80)
    print(f"  Yesterday: {len(REMOVED_TODAY) + len(COMMON_SECURITIES)} securities")
    print(f"  Today: {len(ADDED_TODAY) + len(COMMON_SECURITIES)} securities")
    print(f"  Net change: {len(ADDED_TODAY) - len(REMOVED_TODAY):+d} securities")


def show_feb10_baseline():
    """Show baseline results from Feb 10 for context."""
    print("\n" + "=" * 80)
    print("HISTORICAL CONTEXT - FEB 10 RESULTS (17 securities)")
    print("=" * 80)

    print("\n📊 Signal Distribution (Feb 10):")
    print("  STRONG_SELL: 11 securities (65%)")
    print("  SELL: 0 securities")
    print("  BUY: 1 security (6%)")
    print("  HOLD: 5 securities (29%)")

    print("\n🔴 STRONG_SELL signals (Feb 10):")
    strongsell_feb10 = [
        ("HT8UZB", "Alphabet Inc.", -38.55),
        ("JU5YHH", "Qualcomm Inc.", -63.64),  # REMOVED
        ("HS4P7G", "Amazon.com Inc.", -63.59),
        ("HS765P", "Starbucks Corp.", -45.70),
        ("JU3YAP", "Nasdaq Inc.", -90.48),  # REMOVED
        ("JT2GHE", "Meta Platforms", -54.29),
        ("JK9Z20", "Microsoft Corp.", -83.70),  # REMOVED
        ("MM5J03", "Newmont Corp.", -34.97),
        ("JH5VLN", "Blackrock Inc.", -27.27),
        ("HT93ZB", "Allianz SE", -29.71),
        ("MM0CVV", "Applied Materials", None),  # No data in notes
    ]

    for wkn, name, drawdown in strongsell_feb10:
        removed = " [REMOVED FROM DEPOT]" if wkn in REMOVED_TODAY else ""
        dd_str = f"{drawdown:+.2f}%" if drawdown is not None else "N/A"
        print(f"  • {wkn} - {name}: {dd_str}{removed}")

    print("\n🟢 BUY signal (Feb 10):")
    print("  • MG9VYR - Cisco Systems: -9.27%")

    print("\n🟡 HOLD signals (Feb 10):")
    hold_feb10 = [
        ("JH4WD6", "Apple Inc."),
        ("MK74CT", "GE Aerospace"),
        ("MM2DRR", "EssilorLuxottica"),
        ("JK9V0Y", "Nvidia Corp."),
    ]
    for wkn, name in hold_feb10:
        print(f"  • {wkn} - {name}")

    print("\n💡 Key Insights from Feb 10:")
    print("  • 4 worst performers removed: JU5YHH (-64%), JU3YAP (-90%), ")
    print("    HT5D3H (Walmart), JK9Z20 (-84%)")
    print("  • 2 new positions added: MJ5417 (Regeneron), PK64FA (KLA)")
    print("  • Net effect: Reduced exposure from 17 to 15 securities")
    print("  • Removed avg drawdown: ~-80% (major losers)")


if __name__ == "__main__":
    analyze_chart_availability()
    show_feb10_baseline()

    print("\n" + "=" * 80)
    print("NOTES")
    print("=" * 80)
    print("  📌 Yesterday (Feb 12) charts exist but structured output was not saved")
    print("  📌 Current run will show today's (Feb 13) results")
    print("  📌 The depot cleanup removed 4 major losers (-64% to -90% drawdown)")
    print("  📌 Expect fewer STRONG_SELL signals with the cleaned depot")
    print("=" * 80)
