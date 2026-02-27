"""Show all signal recommendations from latest results."""

from pathlib import Path

import pandas as pd

# Find latest result file
results_dir = Path("results")
files = sorted(results_dir.glob("mega_trend_folger_*.xlsx"), reverse=True)

if not files:
    print("No results found")
    exit()

latest = files[0]
print(f"Reading: {latest.name}\n")

df = pd.read_excel(latest)

strong_sells = df[df["Trend Signal"] == "STRONG_SELL"]
sells = df[df["Trend Signal"] == "SELL"]
holds = df[df["Trend Signal"] == "HOLD"]
buys = df[df["Trend Signal"] == "BUY"]

print("=" * 80)
print(f"SIGNAL DISTRIBUTION (Total: {len(df)} securities)")
print("=" * 80)
print(f"  STRONG_SELL: {len(strong_sells)} ({len(strong_sells) / len(df) * 100:.1f}%)")
print(f"  SELL: {len(sells)} ({len(sells) / len(df) * 100:.1f}%)")
print(f"  HOLD: {len(holds)} ({len(holds) / len(df) * 100:.1f}%)")
print(f"  BUY: {len(buys)} ({len(buys) / len(df) * 100:.1f}%)")

print("\n" + "=" * 80)
print(f"🚨 STRONG_SELL RECOMMENDATIONS ({len(strong_sells)} securities)")
print("=" * 80)
if len(strong_sells) > 0:
    for _, row in strong_sells.iterrows():
        print(f"\n{row['WKN']} - {row['Name']}")
        print(f"  Price: {row['Current Price']:.2f} EUR")
        print(f"  Drawdown: {row['Drawdown %']:.2%}")
        print(f"  ADX: {row['ADX']:.1f}")
        print(f"  Execution: {row['Execution Recommendation']}")
        print(f"  Reason: {row['Reason']}")
else:
    print("  None")

print("\n" + "=" * 80)
print(f"⚠️  SELL RECOMMENDATIONS ({len(sells)} securities)")
print("=" * 80)
if len(sells) > 0:
    for _, row in sells.iterrows():
        print(f"\n{row['WKN']} - {row['Name']}")
        print(f"  Price: {row['Current Price']:.2f} EUR")
        print(f"  Drawdown: {row['Drawdown %']:.2%}")
        print(f"  ADX: {row['ADX']:.1f}")
        print(f"  Execution: {row['Execution Recommendation']}")
        print(f"  Reason: {row['Reason']}")
else:
    print("  None")

print("\n" + "=" * 80)
print(f"✅ BUY RECOMMENDATIONS ({len(buys)} securities)")
print("=" * 80)
if len(buys) > 0:
    for _, row in buys.iterrows():
        print(f"\n{row['WKN']} - {row['Name']}")
        print(f"  Price: {row['Current Price']:.2f} EUR")
        print(f"  Drawdown: {row['Drawdown %']:.2%}")
        print(f"  ADX: {row['ADX']:.1f}")
        print(f"  Execution: {row['Execution Recommendation']}")
        print(f"  Reason: {row['Reason']}")
else:
    print("  None")

print("\n" + "=" * 80)
print(f"📊 HOLD RECOMMENDATIONS ({len(holds)} securities)")
print("=" * 80)
if len(holds) > 0:
    for _, row in holds.iterrows():
        print(f"\n{row['WKN']} - {row['Name']}")
        print(f"  Price: {row['Current Price']:.2f} EUR")
        print(f"  Drawdown: {row['Drawdown %']:.2%}")
        print(f"  ADX: {row['ADX']:.1f}")
        print(f"  Reason: {row['Reason'][:100]}...")
else:
    print("  None")

print("\n" + "=" * 80)
