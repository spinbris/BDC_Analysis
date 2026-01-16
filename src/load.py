"""Load and filter BDC data"""

from pathlib import Path
from typing import Optional

import pandas as pd


# Top 10 BDCs by fair value
TOP_10_BDCS = {
    1287750: {"ticker": "ARCC", "name": "Ares Capital Corporation"},
    1631115: {"ticker": "FSK",  "name": "FS KKR Capital Corp"},
    1838831: {"ticker": "BXSL", "name": "Blackstone Secured Lending Fund"},
    1758190: {"ticker": "ORCC", "name": "Blue Owl Capital Corporation"},
    1476765: {"ticker": "GBDC", "name": "Golub Capital BDC Inc"},
    1287032: {"ticker": "PSEC", "name": "Prospect Capital Corporation"},
    1396440: {"ticker": "MAIN", "name": "Main Street Capital Corporation"},
    1280784: {"ticker": "HTGC", "name": "Hercules Capital Inc"},
    1496099: {"ticker": "NMFC", "name": "New Mountain Finance Corporation"},
    1414932: {"ticker": "OCSL", "name": "Oaktree Specialty Lending Corporation"},
}

TOP_10_CIKS = list(TOP_10_BDCS.keys())


def load_submissions(data_dir: Path) -> pd.DataFrame:
    """Load submission metadata (sub.tsv)

    Args:
        data_dir: Path to directory containing sub.tsv

    Returns:
        DataFrame with BDC submission metadata
    """
    sub_path = Path(data_dir) / "sub.tsv"

    if not sub_path.exists():
        raise FileNotFoundError(f"sub.tsv not found at {sub_path}")

    print(f"Loading submissions from {sub_path}...")
    df = pd.read_csv(sub_path, sep='\t', low_memory=False)

    print(f"✓ Loaded {len(df):,} submissions")
    print(f"  Columns: {', '.join(df.columns[:10])}" + (" ..." if len(df.columns) > 10 else ""))

    return df


def load_soi(data_dir: Path) -> pd.DataFrame:
    """Load Schedule of Investments (soi.tsv)

    Args:
        data_dir: Path to directory containing soi.tsv

    Returns:
        DataFrame with portfolio holdings data
    """
    soi_path = Path(data_dir) / "soi.tsv"

    if not soi_path.exists():
        raise FileNotFoundError(f"soi.tsv not found at {soi_path}")

    print(f"Loading Schedule of Investments from {soi_path}...")
    df = pd.read_csv(soi_path, sep='\t', low_memory=False)

    print(f"✓ Loaded {len(df):,} investment records")
    print(f"  Columns: {len(df.columns)}")

    return df


def filter_top_bdcs(
    soi_df: pd.DataFrame,
    sub_df: pd.DataFrame,
    ciks: Optional[list] = None
) -> pd.DataFrame:
    """Filter SOI data to specified BDCs

    Args:
        soi_df: Schedule of Investments DataFrame
        sub_df: Submissions DataFrame
        ciks: List of CIKs to filter (default: TOP_10_CIKS)

    Returns:
        Filtered SOI DataFrame with only specified BDCs
    """
    if ciks is None:
        ciks = TOP_10_CIKS

    print(f"\nFiltering to {len(ciks)} BDCs...")

    # Convert CIKs to int if needed
    if 'cik' in soi_df.columns:
        soi_df['cik'] = pd.to_numeric(soi_df['cik'], errors='coerce')

    filtered = soi_df[soi_df['cik'].isin(ciks)].copy()

    print(f"✓ Filtered to {len(filtered):,} records")

    # Show BDC counts
    bdc_counts = filtered['cik'].value_counts().sort_index()
    print(f"\nRecords per BDC:")
    for cik, count in bdc_counts.items():
        bdc_info = TOP_10_BDCS.get(int(cik), {"ticker": "???", "name": "Unknown"})
        print(f"  {bdc_info['ticker']:6} (CIK {cik}): {count:,} records")

    return filtered


if __name__ == "__main__":
    # Test loading
    from pathlib import Path

    data_dir = Path(__file__).parent.parent / "data" / "raw" / "bdc-data-sets"

    sub_df = load_submissions(data_dir)
    soi_df = load_soi(data_dir)
    filtered_soi = filter_top_bdcs(soi_df, sub_df)

    print(f"\n✓ Load test complete")
    print(f"  Submissions: {len(sub_df):,} rows")
    print(f"  SOI (all): {len(soi_df):,} rows")
    print(f"  SOI (top 10): {len(filtered_soi):,} rows")
