"""
Analyze industry concentration within and across BDCs
Run: python -m src.analyze_industry_concentration
"""

import pandas as pd
import numpy as np

print("=" * 70)
print("BDC INDUSTRY CONCENTRATION ANALYSIS")
print("=" * 70)

# Load data
df = pd.read_csv('outputs/all_bdc_holdings_with_industry.csv')

# Filter to BDCs with business descriptions
bdcs_with_data = ['Ares Capital Corporation', 'Main Street Capital Corporation']
df_with_industry = df[df['bdc_name'].isin(bdcs_with_data)].copy()

print(f"\nAnalyzing {len(df_with_industry):,} holdings from {len(bdcs_with_data)} BDCs")
print(f"BDCs: {', '.join(bdcs_with_data)}")

# Aggregate to company level (to avoid double-counting multiple tranches)
print("\nAggregating to unique company level...")
company_level = df_with_industry.groupby(['bdc_name', 'company_name', 'industry_sector']).agg({
    'fair_value': 'sum',
    'principal': 'sum',
    'cost': 'sum'
}).reset_index()

print(f"✓ {len(company_level):,} unique companies")

# Industry breakdown by BDC
print("\n" + "=" * 70)
print("INDUSTRY CONCENTRATION BY BDC (Fair Value)")
print("=" * 70)

for bdc in sorted(company_level['bdc_name'].unique()):
    bdc_df = company_level[company_level['bdc_name'] == bdc]
    total_fv = bdc_df['fair_value'].sum()
    total_companies = len(bdc_df)

    print(f"\n{bdc}:")
    print(f"Total Companies: {total_companies:,}")
    print(f"Total Fair Value: ${total_fv/1e9:.2f}B")
    print("-" * 70)

    industry_totals = bdc_df.groupby('industry_sector').agg({
        'fair_value': 'sum',
        'company_name': 'count'
    }).rename(columns={'company_name': 'companies'})
    industry_totals = industry_totals.sort_values('fair_value', ascending=False)

    # Exclude Unknown for concentration metrics
    industry_totals_known = industry_totals[industry_totals.index != 'Unknown']

    print(f"\n{'Industry':<30} {'Companies':>10} {'Fair Value':>15} {'% of Total':>12}")
    print("-" * 70)

    for industry, row in industry_totals.head(10).iterrows():
        fv = row['fair_value']
        companies = int(row['companies'])
        pct = (fv / total_fv * 100) if total_fv > 0 else 0
        print(f"{industry:<30} {companies:>10} ${fv/1e9:>13.2f}B {pct:>11.1f}%")

# Cross-BDC industry analysis
print("\n" + "=" * 70)
print("CROSS-BDC INDUSTRY EXPOSURE")
print("=" * 70)

# Pivot: industry × BDC (company count)
print("\n1. Number of Companies by Industry and BDC:")
print("-" * 70)
industry_by_bdc_count = company_level.groupby(['industry_sector', 'bdc_name']).size().unstack(fill_value=0)
industry_by_bdc_count['Total'] = industry_by_bdc_count.sum(axis=1)
industry_by_bdc_count = industry_by_bdc_count.sort_values('Total', ascending=False)

print(industry_by_bdc_count.head(15).to_string())

# Pivot: industry × BDC (fair value)
print("\n\n2. Fair Value ($B) by Industry and BDC:")
print("-" * 70)
industry_by_bdc_fv = company_level.groupby(['industry_sector', 'bdc_name'])['fair_value'].sum().unstack(fill_value=0) / 1e9
industry_by_bdc_fv['Total'] = industry_by_bdc_fv.sum(axis=1)
industry_by_bdc_fv = industry_by_bdc_fv.sort_values('Total', ascending=False)

print(industry_by_bdc_fv.head(15).to_string())

# Industry overlap analysis (companies held by both BDCs in same industry)
print("\n" + "=" * 70)
print("INDUSTRY-LEVEL OVERLAP ANALYSIS")
print("=" * 70)

# For each industry, find companies held by both BDCs
overlap_results = []

for industry in company_level['industry_sector'].unique():
    if industry == 'Unknown':
        continue

    industry_companies = company_level[company_level['industry_sector'] == industry]

    arcc_companies = set(industry_companies[industry_companies['bdc_name'] == 'Ares Capital Corporation']['company_name'])
    main_companies = set(industry_companies[industry_companies['bdc_name'] == 'Main Street Capital Corporation']['company_name'])

    overlap = arcc_companies & main_companies
    total_unique = len(arcc_companies | main_companies)

    overlap_results.append({
        'industry': industry,
        'arcc_count': len(arcc_companies),
        'main_count': len(main_companies),
        'overlap_count': len(overlap),
        'total_unique': total_unique,
        'overlap_pct': (len(overlap) / total_unique * 100) if total_unique > 0 else 0,
        'overlapping_companies': ', '.join(sorted(overlap)) if overlap else 'None'
    })

overlap_df = pd.DataFrame(overlap_results).sort_values('overlap_count', ascending=False)

print("\nIndustries with Company Overlap between ARCC and MAIN:")
print("-" * 70)
print(f"{'Industry':<25} {'ARCC':>6} {'MAIN':>6} {'Overlap':>8} {'% Overlap':>10}")
print("-" * 70)

for _, row in overlap_df.head(15).iterrows():
    print(f"{row['industry']:<25} {row['arcc_count']:>6} {row['main_count']:>6} {row['overlap_count']:>8} {row['overlap_pct']:>9.1f}%")

# Show overlapping companies
overlaps_found = overlap_df[overlap_df['overlap_count'] > 0]
if len(overlaps_found) > 0:
    print("\n\nCompanies Held by Both BDCs (by Industry):")
    print("=" * 70)
    for _, row in overlaps_found.iterrows():
        print(f"\n{row['industry']}:")
        print(f"  {row['overlapping_companies']}")

# Concentration metrics
print("\n" + "=" * 70)
print("INDUSTRY CONCENTRATION METRICS")
print("=" * 70)

# Herfindahl-Hirschman Index (HHI) for each BDC
for bdc in sorted(company_level['bdc_name'].unique()):
    bdc_df = company_level[company_level['bdc_name'] == bdc]

    # Exclude Unknown
    bdc_df_known = bdc_df[bdc_df['industry_sector'] != 'Unknown']

    if len(bdc_df_known) == 0:
        continue

    total_fv = bdc_df_known['fair_value'].sum()

    # Calculate market share for each industry
    industry_shares = bdc_df_known.groupby('industry_sector')['fair_value'].sum() / total_fv
    hhi = (industry_shares ** 2).sum() * 10000  # Scale to 0-10000

    # Top 3 concentration
    top3_concentration = industry_shares.nlargest(3).sum() * 100

    print(f"\n{bdc}:")
    print(f"  Industries (excl Unknown): {len(industry_shares)}")
    print(f"  HHI: {hhi:.0f} ({'Low' if hhi < 1500 else 'Moderate' if hhi < 2500 else 'High'} concentration)")
    print(f"  Top 3 industries: {top3_concentration:.1f}% of portfolio")
    print(f"  Largest industry: {industry_shares.idxmax()} ({industry_shares.max()*100:.1f}%)")

# Save results
print("\n" + "=" * 70)
print("SAVING RESULTS")
print("=" * 70)

# Save company-level data with industry
industry_by_bdc_count.to_csv('outputs/industry_company_counts_by_bdc.csv')
print("✓ Saved company counts to outputs/industry_company_counts_by_bdc.csv")

industry_by_bdc_fv.to_csv('outputs/industry_fair_value_by_bdc.csv')
print("✓ Saved fair values to outputs/industry_fair_value_by_bdc.csv")

overlap_df.to_csv('outputs/industry_overlap_analysis.csv', index=False)
print("✓ Saved overlap analysis to outputs/industry_overlap_analysis.csv")

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)
