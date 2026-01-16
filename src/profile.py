"""Data profiling to identify identifier columns and data structure"""

from pathlib import Path
from typing import Dict, List

import pandas as pd


def profile_columns(df: pd.DataFrame) -> Dict[str, List[str]]:
    """Categorize columns by likely purpose

    Args:
        df: DataFrame to profile

    Returns:
        Dict with categories: metadata, identifiers, values, text, other
    """
    # Patterns to identify column types
    identifier_patterns = [
        'cusip', 'lei', 'cik', 'ticker', 'isin', 'identifier', 'id',
        'figi', 'sedol', 'ric', 'permid'
    ]
    metadata_patterns = ['adsh', 'form', 'date', 'period', 'filed', 'report']
    value_patterns = ['value', 'amount', 'cost', 'price', 'fair', 'carrying']
    text_patterns = ['name', 'description', 'title', 'industry', 'sector', 'type']

    categories = {
        'identifiers': [],
        'metadata': [],
        'values': [],
        'text': [],
        'other': []
    }

    for col in df.columns:
        col_lower = col.lower()

        # Check identifier patterns first (highest priority)
        if any(p in col_lower for p in identifier_patterns):
            categories['identifiers'].append(col)
        elif any(p in col_lower for p in metadata_patterns):
            categories['metadata'].append(col)
        elif any(p in col_lower for p in value_patterns):
            categories['values'].append(col)
        elif any(p in col_lower for p in text_patterns):
            categories['text'].append(col)
        else:
            categories['other'].append(col)

    return categories


def check_identifier_coverage(df: pd.DataFrame) -> pd.DataFrame:
    """Analyze population rates for potential identifier columns

    Args:
        df: DataFrame to analyze

    Returns:
        DataFrame with columns: column_name, populated, total, pct_populated, sample_value
    """
    # Find potential identifier columns
    identifier_patterns = [
        'cusip', 'lei', 'cik', 'ticker', 'isin', 'identifier', 'id',
        'figi', 'sedol', 'ric', 'permid'
    ]

    id_columns = [
        col for col in df.columns
        if any(p in col.lower() for p in identifier_patterns)
    ]

    if not id_columns:
        print("⚠ No identifier columns found matching common patterns")
        return pd.DataFrame()

    results = []
    total = len(df)

    for col in id_columns:
        populated = df[col].notna().sum()
        pct = (populated / total * 100) if total > 0 else 0

        # Get a sample non-null value
        sample = df[col].dropna().iloc[0] if populated > 0 else None

        results.append({
            'column_name': col,
            'populated': populated,
            'total': total,
            'pct_populated': round(pct, 1),
            'sample_value': sample
        })

    results_df = pd.DataFrame(results).sort_values('populated', ascending=False)
    return results_df


def generate_data_profile_report(
    soi_df: pd.DataFrame,
    output_path: Path
) -> None:
    """Generate DATA_PROFILE.md report

    Args:
        soi_df: Schedule of Investments DataFrame
        output_path: Path to write DATA_PROFILE.md
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\nGenerating data profile report...")

    # Profile columns
    categories = profile_columns(soi_df)
    identifier_coverage = check_identifier_coverage(soi_df)

    # Get sample company names
    name_columns = [col for col in soi_df.columns if 'name' in col.lower()]
    sample_names = []
    if name_columns:
        primary_name_col = name_columns[0]
        sample_names = soi_df[primary_name_col].dropna().head(10).tolist()

    # Write report
    with open(output_path, 'w') as f:
        f.write("# BDC Data Profile Report\n\n")
        f.write(f"**Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Records analyzed:** {len(soi_df):,}\n\n")

        f.write("---\n\n")
        f.write("## Dataset Overview\n\n")
        f.write(f"**Total columns:** {len(soi_df.columns)}\n")
        f.write(f"**Total records:** {len(soi_df):,}\n\n")

        f.write("### Column Categories\n\n")
        for category, cols in categories.items():
            f.write(f"**{category.title()}:** {len(cols)} columns\n")
        f.write("\n")

        f.write("---\n\n")
        f.write("## Identifier Column Analysis\n\n")

        if not identifier_coverage.empty:
            f.write("Available identifier columns and their population rates:\n\n")
            f.write("| Column | Populated | Total | % Populated | Sample Value |\n")
            f.write("|--------|-----------|-------|-------------|-------------|\n")

            for _, row in identifier_coverage.iterrows():
                f.write(f"| {row['column_name']} | {row['populated']:,} | {row['total']:,} | "
                       f"{row['pct_populated']:.1f}% | {row['sample_value']} |\n")

            f.write("\n")
        else:
            f.write("⚠ **No identifier columns found**\n\n")
            f.write("The data does not contain standard identifier columns (CUSIP, LEI, CIK, etc.).\n")
            f.write("Entity matching will rely entirely on name-based matching.\n\n")

        f.write("---\n\n")
        f.write("## Column Inventory\n\n")

        for category, cols in categories.items():
            if cols:
                f.write(f"### {category.title()} Columns ({len(cols)})\n\n")
                for col in sorted(cols):
                    f.write(f"- `{col}`\n")
                f.write("\n")

        f.write("---\n\n")
        f.write("## Company Name Samples\n\n")

        if sample_names:
            f.write(f"Sample values from `{name_columns[0]}` column:\n\n")
            for i, name in enumerate(sample_names, 1):
                f.write(f"{i}. {name}\n")
            f.write("\n")

        f.write("---\n\n")
        f.write("## Recommendations for Phase 2\n\n")

        if not identifier_coverage.empty:
            high_coverage = identifier_coverage[identifier_coverage['pct_populated'] > 50]
            medium_coverage = identifier_coverage[
                (identifier_coverage['pct_populated'] >= 20) &
                (identifier_coverage['pct_populated'] <= 50)
            ]

            if not high_coverage.empty:
                f.write("### Scenario A: Good Identifier Coverage\n\n")
                f.write("The following identifiers have >50% population:\n\n")
                for _, row in high_coverage.iterrows():
                    f.write(f"- `{row['column_name']}`: {row['pct_populated']:.1f}% populated\n")
                f.write("\n**Recommended matching strategy:**\n")
                f.write("1. Match by identifier first (covers majority)\n")
                f.write("2. Exact name match for remainder\n")
                f.write("3. Minimal fuzzy matching needed\n\n")

            elif not medium_coverage.empty:
                f.write("### Scenario B: Moderate Identifier Coverage\n\n")
                f.write("Identifiers available but with moderate coverage (20-50%):\n\n")
                for _, row in medium_coverage.iterrows():
                    f.write(f"- `{row['column_name']}`: {row['pct_populated']:.1f}% populated\n")
                f.write("\n**Recommended matching strategy:**\n")
                f.write("1. Match by identifier where available\n")
                f.write("2. Exact name match\n")
                f.write("3. Normalized name match\n")
                f.write("4. Fuzzy match for remaining ~50%\n\n")

            else:
                f.write("### Scenario C: Poor Identifier Coverage\n\n")
                f.write("Identifiers present but rarely populated (<20%).\n\n")
                f.write("**Recommended matching strategy:**\n")
                f.write("1. Exact name match first\n")
                f.write("2. Normalized name match second\n")
                f.write("3. Fuzzy match as fallback with manual review\n")
                f.write("4. Industry matching as secondary signal\n\n")
        else:
            f.write("### No Identifier Columns Available\n\n")
            f.write("**Recommended matching strategy:**\n")
            f.write("1. Exact name match first\n")
            f.write("2. Normalized name match (remove punctuation, standardize suffixes)\n")
            f.write("3. Fuzzy matching with manual review (threshold 90+)\n")
            f.write("4. Industry/sector as tie-breaker\n\n")

    print(f"✓ Report written to {output_path}")


if __name__ == "__main__":
    # Test profiling
    from pathlib import Path
    from src.load import load_soi

    data_dir = Path(__file__).parent.parent / "data" / "raw" / "bdc-data-sets"
    soi_df = load_soi(data_dir)

    # Profile
    print("\n" + "="*60)
    print("COLUMN CATEGORIZATION")
    print("="*60)
    categories = profile_columns(soi_df)
    for cat, cols in categories.items():
        print(f"\n{cat.upper()} ({len(cols)}):")
        for col in sorted(cols)[:5]:  # Show first 5
            print(f"  - {col}")
        if len(cols) > 5:
            print(f"  ... and {len(cols) - 5} more")

    print("\n" + "="*60)
    print("IDENTIFIER COVERAGE")
    print("="*60)
    coverage = check_identifier_coverage(soi_df)
    if not coverage.empty:
        print(coverage.to_string(index=False))
    else:
        print("No identifier columns found")

    # Generate report
    output_path = Path(__file__).parent.parent / "Docs" / "DATA_PROFILE.md"
    generate_data_profile_report(soi_df, output_path)
