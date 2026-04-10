"""Compare warrant recommendations with their underlying stock recommendations."""

from pathlib import Path

import pandas as pd

# Mapping of warrants to their underlying stocks
WARRANT_TO_UNDERLYING = {
    "HT8UZB": "A14Y6H",  # Alphabet Inc.
    "HS4P7G": "906866",  # Amazon.com Inc.
    "JT2GHE": "A1JWVX",  # Meta Platforms Inc.
    "JH4WD6": "865985",  # Apple Inc.
    "HS765P": "884437",  # Starbucks Corporation
    "MK74CT": "A3CSML",  # GE Aerospace & Defense
    "MM2DRR": "863195",  # EssilorLuxottica S.A.
    "MG9VYR": "878841",  # Cisco Systems Inc.
    "JK9V0Y": "918422",  # Nvidia Corporation
    "MM5J03": "853823",  # Newmont Corporation
    "JH5VLN": "A40PW4",  # Blackrock Inc.
    "HT93ZB": "840400",  # Allianz SE
    "MM0CVV": "865177",  # Applied Materials Inc.
    "PK64FA": "865884",  # KLA Corp.
}


def load_latest_results(depot_name: str) -> pd.DataFrame:
    """Load the most recent results for a depot."""
    results_dir = Path("results")
    files = sorted(results_dir.glob(f"{depot_name}_*.xlsx"), reverse=True)

    if not files:
        raise FileNotFoundError(f"No results found for {depot_name}")

    # Try files until we find one with the expected WKN format
    for file in files:
        df = pd.read_excel(file)
        if not df.empty and "WKN" in df.columns:
            # Check if this file contains warrants (WKNs start with letters) or stocks (start with country codes)
            first_wkn = str(df["WKN"].iloc[0])
            if depot_name == "mega_trend_folger":
                # Warrants have WKNs like HT8UZB, HS4P7G, etc.
                if len(first_wkn) == 6 and first_wkn[0].isalpha() and first_wkn[1].isalpha():
                    print(f"Loading: {file.name}")
                    return df
            else:
                # Underlyings have ISINs like US02079K1079
                if len(first_wkn) > 6:
                    print(f"Loading: {file.name}")
                    return df

    # If no suitable file found, use the first one
    latest_file = files[0]
    print(f"Loading: {latest_file.name}")
    df = pd.read_excel(latest_file)
    return df


def compare_recommendations():
    """Compare warrant and underlying recommendations."""
    print("=" * 100)
    print("WARRANT vs UNDERLYING STOCK COMPARISON")
    print("=" * 100)

    try:
        # Load warrant results
        print("\n📊 Loading warrant results (mega_trend_folger)...")
        warrants_df = load_latest_results("mega_trend_folger")

        # Load underlying results
        print("📊 Loading underlying stock results (mtf_underlyings)...")
        underlyings_df = load_latest_results("mtf_underlyings")

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("   Please ensure both analyses have been run.")
        return

    # Create comparison
    print("\n" + "=" * 100)
    print("DETAILED COMPARISON BY SECURITY")
    print("=" * 100)

    comparisons = []

    for warrant_wkn, underlying_isin in WARRANT_TO_UNDERLYING.items():
        # Find warrant data
        warrant_row = warrants_df[warrants_df["WKN"] == warrant_wkn]
        if warrant_row.empty:
            print(f"\n⚠️  Warrant {warrant_wkn} not found in results")
            continue

        # Find underlying data
        underlying_row = underlyings_df[underlyings_df["WKN"] == underlying_isin]
        if underlying_row.empty:
            print(f"\n⚠️  Underlying {underlying_isin} not found in results")
            continue

        warrant_row = warrant_row.iloc[0]
        underlying_row = underlying_row.iloc[0]

        # Extract comparison data
        company_name = warrant_row["Name"].split("Call")[0].strip().split()[-2:]
        company_name = " ".join(company_name) if len(company_name) > 1 else warrant_row["Name"]

        comparison = {
            "Warrant WKN": warrant_wkn,
            "Underlying WKN": underlying_isin,
            "Company": company_name,
            "Warrant Signal": warrant_row["Trend Signal"],
            "Stock Signal": underlying_row["Trend Signal"],
            "Warrant Recommendation": warrant_row["Recommendation"][:20] + "...",
            "Stock Recommendation": underlying_row["Recommendation"][:20] + "...",
            "Warrant Drawdown": warrant_row["Drawdown %"],
            "Stock Drawdown": underlying_row["Drawdown %"],
            "Warrant ADX": warrant_row["ADX"],
            "Stock ADX": underlying_row["ADX"],
            "Agreement": (
                "✅ YES"
                if warrant_row["Trend Signal"] == underlying_row["Trend Signal"]
                else "❌ NO"
            ),
        }
        comparisons.append(comparison)

        # Print detailed comparison
        print(f"\n{'─' * 100}")
        print(f"🏢 {company_name}")
        print(f"{'─' * 100}")
        print(f"  Warrant (WKN: {warrant_wkn}):")
        print(f"    Trend Signal:    {warrant_row['Trend Signal']}")
        print(f"    Drawdown:        {warrant_row['Drawdown %']:.2%}")
        print(f"    ADX:             {warrant_row['ADX']:.1f}")
        print(f"    Price:           {warrant_row['Current Price']:.2f} €")
        print(f"    Recommendation:  {warrant_row['Recommendation'][:60]}...")
        print()
        print(f"  Underlying Stock (WKN: {underlying_isin}):")
        print(f"    Trend Signal:    {underlying_row['Trend Signal']}")
        print(f"    Drawdown:        {underlying_row['Drawdown %']:.2%}")
        print(f"    ADX:             {underlying_row['ADX']:.1f}")
        print(f"    Price:           {underlying_row['Current Price']:.2f} €")
        print(f"    Recommendation:  {underlying_row['Recommendation'][:60]}...")
        print()
        print(f"  Signal Agreement: {comparison['Agreement']}")

        # Highlight significant discrepancies
        if warrant_row["Trend Signal"] != underlying_row["Trend Signal"]:
            print(
                f"  ⚠️  DISCREPANCY: Warrant shows {warrant_row['Trend Signal']}, Stock shows {underlying_row['Trend Signal']}"
            )

    # Check if we have any comparisons
    if not comparisons:
        print(
            "\n❌ No comparisons could be made. Please ensure both analyses contain matching securities."
        )
        return

    # Summary statistics
    print("\n" + "=" * 100)
    print("SUMMARY STATISTICS")
    print("=" * 100)

    comp_df = pd.DataFrame(comparisons)

    # Signal distribution
    print("\n📊 Trend Signal Distribution:")
    print("\n  Warrants:")
    for signal, count in comp_df["Warrant Signal"].value_counts().items():
        print(f"    {signal}: {count} ({count / len(comp_df) * 100:.1f}%)")

    print("\n  Underlying Stocks:")
    for signal, count in comp_df["Stock Signal"].value_counts().items():
        print(f"    {signal}: {count} ({count / len(comp_df) * 100:.1f}%)")

    # Agreement rate
    agreements = comp_df["Agreement"].str.contains("YES").sum()
    total = len(comp_df)
    print(f"\n🎯 Signal Agreement Rate: {agreements}/{total} ({agreements / total * 100:.1f}%)")

    # Where they disagree
    disagreements = comp_df[comp_df["Agreement"].str.contains("NO")]
    if not disagreements.empty:
        print(f"\n❌ Disagreements ({len(disagreements)} cases):")
        for _, row in disagreements.iterrows():
            print(
                f"  • {row['Company']}: Warrant={row['Warrant Signal']}, Stock={row['Stock Signal']}"
            )

    # Average drawdowns
    print("\n📉 Average Drawdown:")
    print(f"  Warrants: {comp_df['Warrant Drawdown'].mean():.2%}")
    print(f"  Stocks:   {comp_df['Stock Drawdown'].mean():.2%}")

    # Average ADX
    print("\n📈 Average ADX (Trend Strength):")
    print(f"  Warrants: {comp_df['Warrant ADX'].mean():.1f}")
    print(f"  Stocks:   {comp_df['Stock ADX'].mean():.1f}")

    print("\n" + "=" * 100)


if __name__ == "__main__":
    compare_recommendations()
