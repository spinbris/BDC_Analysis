"""
Analyze portfolio overlap across successfully parsed BDCs
Run: python -m src.analyze_overlap
"""

import pandas as pd
from src.overlap import (
    build_holdings_matrix,
    find_common_holdings,
    calculate_bdc_overlap_matrix,
    get_overlap_summary
)

print("=" * 60)
print("BDC PORTFOLIO OVERLAP ANALYSIS")
print("=" * 60)

# Load combined holdings
holdings_path = 'outputs/all_bdc_holdings.csv'
print(f"\nLoading holdings from {holdings_path}...")
df = pd.read_csv(holdings_path)

print(f"✓ Loaded {len(df):,} holdings across {df['bdc_name'].nunique()} BDCs")
print(f"\nBDCs in dataset:")
for bdc_name in df['bdc_name'].unique():
    count = len(df[df['bdc_name'] == bdc_name])
    total_fv = df[df['bdc_name'] == bdc_name]['fair_value'].sum()
    print(f"  - {bdc_name}: {count} holdings, ${total_fv/1_000_000_000:.2f}B")

# Build holdings matrix (binary: 1 if BDC holds company, 0 otherwise)
print("\n" + "=" * 60)
print("BUILDING HOLDINGS MATRIX")
print("=" * 60)

matrix = build_holdings_matrix(
    df,
    company_col='company_name',
    bdc_col='bdc_name'
)

# Find common holdings (companies held by 2+ BDCs)
print("\n" + "=" * 60)
print("IDENTIFYING COMMON HOLDINGS")
print("=" * 60)

common_2plus = find_common_holdings(matrix, min_holders=2)
print(f"\nTop 20 most commonly held companies:")
print(common_2plus.head(20).to_string(index=False))

# Find companies held by 3+ BDCs
common_3plus = find_common_holdings(matrix, min_holders=3)
if len(common_3plus) > 0:
    print(f"\n\nCompanies held by 3+ BDCs ({len(common_3plus)} total):")
    print(common_3plus.head(20).to_string(index=False))
else:
    print(f"\n\nNo companies held by 3+ BDCs")

# BDC × BDC overlap matrix
print("\n" + "=" * 60)
print("BDC × BDC OVERLAP MATRIX")
print("=" * 60)

overlap_matrix = calculate_bdc_overlap_matrix(matrix)
print("\nNumber of shared portfolio companies between each BDC pair:")
print(overlap_matrix.to_string())

# Summary statistics
print("\n" + "=" * 60)
print("BDC OVERLAP SUMMARY")
print("=" * 60)

summary = get_overlap_summary(matrix)
summary_with_names = summary.merge(
    df[['bdc_name', 'bdc_cik']].drop_duplicates(),
    left_on='bdc_cik',
    right_on='bdc_name',
    how='left'
)
summary_with_names = summary_with_names[['bdc_name', 'total_companies', 'shared_companies', 'pct_shared']]
print("\nHow many portfolio companies each BDC shares with others:")
print(summary_with_names.to_string(index=False))

# Concentration risk metrics
print("\n" + "=" * 60)
print("CONCENTRATION RISK METRICS")
print("=" * 60)

total_unique_companies = len(matrix)
total_positions = df.shape[0]
avg_holders_per_company = matrix.sum(axis=1).mean()

print(f"\nTotal unique portfolio companies: {total_unique_companies:,}")
print(f"Total investment positions: {total_positions:,}")
print(f"Average BDCs per company: {avg_holders_per_company:.2f}")
print(f"\nCompanies held by exactly 1 BDC: {len(matrix[matrix.sum(axis=1) == 1]):,}")
print(f"Companies held by 2+ BDCs: {len(common_2plus):,}")
if len(common_3plus) > 0:
    print(f"Companies held by 3+ BDCs: {len(common_3plus):,}")

concentration_pct = len(common_2plus) / total_unique_companies * 100
print(f"\nConcentration rate: {concentration_pct:.1f}% of companies held by multiple BDCs")

# Save results
print("\n" + "=" * 60)
print("SAVING RESULTS")
print("=" * 60)

common_2plus.to_csv('outputs/common_holdings_2plus.csv', index=False)
print(f"✓ Saved common holdings (2+) to outputs/common_holdings_2plus.csv")

if len(common_3plus) > 0:
    common_3plus.to_csv('outputs/common_holdings_3plus.csv', index=False)
    print(f"✓ Saved common holdings (3+) to outputs/common_holdings_3plus.csv")

overlap_matrix.to_csv('outputs/bdc_overlap_matrix.csv')
print(f"✓ Saved BDC overlap matrix to outputs/bdc_overlap_matrix.csv")

summary_with_names.to_csv('outputs/bdc_overlap_summary.csv', index=False)
print(f"✓ Saved BDC summary to outputs/bdc_overlap_summary.csv")

print("\n" + "=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)
