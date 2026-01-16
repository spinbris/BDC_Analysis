"""Calculate portfolio overlap across BDCs"""

from typing import Optional

import pandas as pd


def build_holdings_matrix(
    soi_df: pd.DataFrame,
    company_col: str,
    bdc_col: str = 'cik',
    value_col: Optional[str] = None
) -> pd.DataFrame:
    """Build company × BDC matrix

    Args:
        soi_df: Schedule of Investments DataFrame
        company_col: Column containing company names
        bdc_col: Column identifying BDCs (default: 'cik')
        value_col: Optional column with fair values (default: binary 1/0)

    Returns:
        DataFrame with companies as rows, BDCs as columns
    """
    print(f"\nBuilding holdings matrix...")
    print(f"  Company identifier: {company_col}")
    print(f"  BDC identifier: {bdc_col}")
    print(f"  Values: {value_col if value_col else 'binary (1/0)'}")

    # Filter to non-null companies
    df = soi_df[[company_col, bdc_col]].copy()
    if value_col:
        df[value_col] = soi_df[value_col]

    df = df[df[company_col].notna()].copy()

    print(f"  Records with company name: {len(df):,}")

    if value_col:
        # Aggregate by company and BDC (sum if multiple positions)
        matrix = df.pivot_table(
            index=company_col,
            columns=bdc_col,
            values=value_col,
            aggfunc='sum',
            fill_value=0
        )
    else:
        # Binary matrix (1 if held, 0 if not)
        df['held'] = 1
        matrix = df.pivot_table(
            index=company_col,
            columns=bdc_col,
            values='held',
            aggfunc='max',
            fill_value=0
        )

    print(f"✓ Matrix: {len(matrix)} companies × {len(matrix.columns)} BDCs")

    return matrix


def find_common_holdings(
    matrix: pd.DataFrame,
    min_holders: int = 2
) -> pd.DataFrame:
    """Find companies held by multiple BDCs

    Args:
        matrix: Holdings matrix (companies × BDCs)
        min_holders: Minimum number of BDCs holding the company

    Returns:
        DataFrame with: company, holder_count, holders (list)
    """
    print(f"\nFinding companies held by {min_holders}+ BDCs...")

    # Convert to binary (handle both binary and value matrices)
    binary_matrix = (matrix > 0).astype(int)

    # Count holders per company
    holder_counts = binary_matrix.sum(axis=1)

    # Filter to companies with enough holders
    common = holder_counts[holder_counts >= min_holders].sort_values(ascending=False)

    print(f"✓ Found {len(common):,} companies held by {min_holders}+ BDCs")

    # Build results with holder lists
    results = []
    for company, count in common.items():
        holders = matrix.columns[binary_matrix.loc[company] > 0].tolist()
        results.append({
            'company': company,
            'holder_count': int(count),
            'holders': holders
        })

    results_df = pd.DataFrame(results)
    return results_df


def calculate_bdc_overlap_matrix(matrix: pd.DataFrame) -> pd.DataFrame:
    """Calculate BDC × BDC overlap matrix

    Args:
        matrix: Holdings matrix (companies × BDCs)

    Returns:
        DataFrame with BDCs on both axes, values = shared company count
    """
    print(f"\nCalculating BDC × BDC overlap matrix...")

    # Convert to binary
    binary_matrix = (matrix > 0).astype(int)

    # Calculate overlap: for each BDC pair, count shared companies
    # This is equivalent to: (BDC_A AND BDC_B).sum() for all pairs
    overlap = binary_matrix.T @ binary_matrix

    print(f"✓ Overlap matrix: {len(overlap)} × {len(overlap)} BDCs")

    return overlap


def get_overlap_summary(matrix: pd.DataFrame) -> pd.DataFrame:
    """Get summary statistics for overlap analysis

    Args:
        matrix: Holdings matrix (companies × BDCs)

    Returns:
        DataFrame with per-BDC summary stats
    """
    binary_matrix = (matrix > 0).astype(int)

    summary = []
    for bdc in matrix.columns:
        holdings = binary_matrix[bdc]
        total_companies = holdings.sum()

        # Count how many of this BDC's holdings are shared
        company_holder_counts = binary_matrix.sum(axis=1)
        shared_holdings = holdings[company_holder_counts > 1].sum()

        summary.append({
            'bdc_cik': bdc,
            'total_companies': int(total_companies),
            'shared_companies': int(shared_holdings),
            'pct_shared': round(shared_holdings / total_companies * 100, 1) if total_companies > 0 else 0
        })

    return pd.DataFrame(summary).sort_values('total_companies', ascending=False)


if __name__ == "__main__":
    # Test overlap analysis
    from pathlib import Path
    from load import load_submissions, load_soi, filter_top_bdcs

    data_dir = Path(__file__).parent.parent / "data" / "raw" / "bdc-data-sets"

    # Load data
    sub_df = load_submissions(data_dir)
    soi_df = load_soi(data_dir)
    filtered_soi = filter_top_bdcs(soi_df, sub_df)

    # Find company name column
    name_cols = [c for c in filtered_soi.columns if 'name' in c.lower()]
    if not name_cols:
        print("ERROR: No company name column found")
        exit(1)

    company_col = name_cols[0]
    print(f"\nUsing company column: {company_col}")

    # Build matrix
    matrix = build_holdings_matrix(filtered_soi, company_col, bdc_col='cik')

    # Find overlaps
    common = find_common_holdings(matrix, min_holders=2)
    print(f"\nTop 10 most commonly held companies:")
    print(common.head(10).to_string(index=False))

    # BDC overlap matrix
    overlap_matrix = calculate_bdc_overlap_matrix(matrix)
    print(f"\nBDC × BDC Overlap Matrix:")
    print(overlap_matrix)

    # Summary
    summary = get_overlap_summary(matrix)
    print(f"\nBDC Summary:")
    print(summary.to_string(index=False))
