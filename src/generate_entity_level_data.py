"""
Generate entity-level CSV files for detailed pivot table analysis
Run: python -m src.generate_entity_level_data
"""

import pandas as pd
import numpy as np

print("=" * 70)
print("GENERATING ENTITY-LEVEL DATA FOR PIVOT ANALYSIS")
print("=" * 70)

# Load holdings with industry classifications
df = pd.read_csv('outputs/all_bdc_holdings_with_industry.csv')
print(f"\nLoaded {len(df):,} holdings")

# ============================================================================
# FILE 1: Investment Position Level (most granular)
# Every investment position with all dimensions including overlap info
# ============================================================================
print("\n" + "=" * 70)
print("FILE 1: INVESTMENT POSITION LEVEL")
print("=" * 70)

# Calculate company-level overlap information
company_bdc_map = df.groupby('company_name')['bdc_name'].apply(list).to_dict()
company_bdc_count = df.groupby('company_name')['bdc_name'].nunique().to_dict()

# Add overlap columns to each position
df_positions = df.copy()
df_positions['holder_count'] = df_positions['company_name'].map(company_bdc_count)
df_positions['is_shared'] = df_positions['holder_count'] > 1
df_positions['other_holders'] = df_positions.apply(
    lambda row: ', '.join([bdc for bdc in company_bdc_map[row['company_name']]
                           if bdc != row['bdc_name']]),
    axis=1
)

# Add useful calculated columns
df_positions['fair_value_millions'] = (df_positions['fair_value'] / 1e6).round(2)
df_positions['principal_millions'] = (df_positions['principal'] / 1e6).round(2)
df_positions['cost_millions'] = (df_positions['cost'] / 1e6).round(2)

# Add classification flags
df_positions['has_business_desc'] = df_positions['business_description'].notna()
df_positions['industry_classified'] = ~df_positions['industry_sector'].isin(['Unknown', 'Other'])

# Reorder columns for usability
position_cols = [
    # Identifiers
    'bdc_name',
    'bdc_cik',
    'company_name',

    # Overlap information
    'holder_count',
    'is_shared',
    'other_holders',

    # Investment details
    'investment_type',
    'industry_sector',
    'business_description',

    # Financial values (millions)
    'fair_value_millions',
    'principal_millions',
    'cost_millions',

    # Financial values (raw)
    'fair_value',
    'principal',
    'cost',

    # Flags
    'has_business_desc',
    'industry_classified',
]

output_path_positions = 'outputs/pivot_investment_positions.csv'
df_positions[position_cols].to_csv(output_path_positions, index=False)
print(f"✓ Created: {output_path_positions}")
print(f"  Rows: {len(df_positions):,}")
print(f"  Columns: {len(position_cols)}")
print(f"  Use for: Detailed analysis of individual investment positions")

# ============================================================================
# FILE 2: Company Level (aggregated by company within each BDC)
# One row per company per BDC
# ============================================================================
print("\n" + "=" * 70)
print("FILE 2: COMPANY LEVEL (BY BDC)")
print("=" * 70)

# Aggregate to company level within each BDC
company_agg = df.groupby(['bdc_name', 'bdc_cik', 'company_name', 'industry_sector']).agg({
    'fair_value': 'sum',
    'principal': 'sum',
    'cost': 'sum',
    'business_description': 'first',
    'investment_type': lambda x: ', '.join(x.dropna().unique()),  # List all investment types
    'bdc_name': 'count'  # Count of positions
}).rename(columns={'bdc_name': 'position_count'}).reset_index()

# Add overlap information
company_agg['holder_count'] = company_agg['company_name'].map(company_bdc_count)
company_agg['is_shared'] = company_agg['holder_count'] > 1
company_agg['other_holders'] = company_agg.apply(
    lambda row: ', '.join([bdc for bdc in company_bdc_map[row['company_name']]
                           if bdc != row['bdc_name']]),
    axis=1
)

# Add in millions
company_agg['fair_value_millions'] = (company_agg['fair_value'] / 1e6).round(2)
company_agg['principal_millions'] = (company_agg['principal'] / 1e6).round(2)
company_agg['cost_millions'] = (company_agg['cost'] / 1e6).round(2)

# Calculate total exposure across BDCs for each company
company_totals = df.groupby('company_name')['fair_value'].sum().to_dict()
company_agg['total_exposure_across_bdcs'] = company_agg['company_name'].map(company_totals) / 1e6

# Add flags
company_agg['has_business_desc'] = company_agg['business_description'].notna()
company_agg['industry_classified'] = ~company_agg['industry_sector'].isin(['Unknown', 'Other'])

# Reorder columns
company_cols = [
    # Identifiers
    'bdc_name',
    'bdc_cik',
    'company_name',

    # Overlap information
    'holder_count',
    'is_shared',
    'other_holders',

    # Company classification
    'industry_sector',
    'business_description',

    # BDC-specific exposure
    'position_count',
    'investment_type',
    'fair_value_millions',
    'principal_millions',
    'cost_millions',

    # Cross-BDC metrics
    'total_exposure_across_bdcs',

    # Raw values
    'fair_value',
    'principal',
    'cost',

    # Flags
    'has_business_desc',
    'industry_classified',
]

output_path_company = 'outputs/pivot_company_level.csv'
company_agg[company_cols].to_csv(output_path_company, index=False)
print(f"✓ Created: {output_path_company}")
print(f"  Rows: {len(company_agg):,}")
print(f"  Columns: {len(company_cols)}")
print(f"  Use for: Company-level analysis, aggregating multiple positions per company")

# ============================================================================
# FILE 3: Unique Company Master (one row per unique company across all BDCs)
# ============================================================================
print("\n" + "=" * 70)
print("FILE 3: UNIQUE COMPANY MASTER")
print("=" * 70)

# Create master company list
unique_companies = df.groupby('company_name').agg({
    'bdc_name': lambda x: ', '.join(sorted(x.unique())),
    'bdc_cik': lambda x: len(x.unique()),
    'industry_sector': 'first',
    'business_description': 'first',
    'fair_value': 'sum',
    'principal': 'sum',
    'cost': 'sum',
}).reset_index()

unique_companies.columns = [
    'company_name',
    'held_by_bdcs',
    'holder_count',
    'industry_sector',
    'business_description',
    'total_fair_value',
    'total_principal',
    'total_cost',
]

# Add position count
position_counts = df.groupby('company_name').size().to_dict()
unique_companies['total_positions'] = unique_companies['company_name'].map(position_counts)

# Add overlap flag
unique_companies['is_shared'] = unique_companies['holder_count'] > 1

# Add in millions
unique_companies['fair_value_millions'] = (unique_companies['total_fair_value'] / 1e6).round(2)
unique_companies['principal_millions'] = (unique_companies['total_principal'] / 1e6).round(2)
unique_companies['cost_millions'] = (unique_companies['total_cost'] / 1e6).round(2)

# Add flags
unique_companies['has_business_desc'] = unique_companies['business_description'].notna()
unique_companies['industry_classified'] = ~unique_companies['industry_sector'].isin(['Unknown', 'Other'])

# Sort by total fair value
unique_companies = unique_companies.sort_values('total_fair_value', ascending=False)

# Reorder columns
unique_cols = [
    'company_name',
    'holder_count',
    'is_shared',
    'held_by_bdcs',
    'industry_sector',
    'business_description',
    'total_positions',
    'fair_value_millions',
    'principal_millions',
    'cost_millions',
    'total_fair_value',
    'total_principal',
    'total_cost',
    'has_business_desc',
    'industry_classified',
]

output_path_unique = 'outputs/pivot_unique_companies.csv'
unique_companies[unique_cols].to_csv(output_path_unique, index=False)
print(f"✓ Created: {output_path_unique}")
print(f"  Rows: {len(unique_companies):,}")
print(f"  Columns: {len(unique_cols)}")
print(f"  Use for: Cross-BDC company analysis, identifying shared holdings")

# ============================================================================
# FILE 4: BDC-Company Matrix (for quick pivot analysis)
# ============================================================================
print("\n" + "=" * 70)
print("FILE 4: BDC-COMPANY MATRIX")
print("=" * 70)

# Create pivot: companies × BDCs (fair value)
bdc_company_matrix = df.groupby(['company_name', 'bdc_name'])['fair_value'].sum().unstack(fill_value=0)
bdc_company_matrix = bdc_company_matrix / 1e6  # Convert to millions
bdc_company_matrix['Total'] = bdc_company_matrix.sum(axis=1)
bdc_company_matrix['Holder_Count'] = (bdc_company_matrix.iloc[:, :-1] > 0).sum(axis=1)
bdc_company_matrix = bdc_company_matrix.sort_values('Total', ascending=False)

# Add industry
industry_map = df.groupby('company_name')['industry_sector'].first().to_dict()
bdc_company_matrix.insert(0, 'Industry', bdc_company_matrix.index.map(industry_map))

output_path_matrix = 'outputs/pivot_bdc_company_matrix.csv'
bdc_company_matrix.to_csv(output_path_matrix)
print(f"✓ Created: {output_path_matrix}")
print(f"  Rows: {len(bdc_company_matrix):,}")
print(f"  Columns: {len(bdc_company_matrix.columns)}")
print(f"  Use for: Cross-BDC comparison, identifying overlaps, matrix analysis")

# ============================================================================
# FILE 5: Industry-BDC Summary (for industry analysis)
# ============================================================================
print("\n" + "=" * 70)
print("FILE 5: INDUSTRY-BDC DETAIL")
print("=" * 70)

# Aggregate at company level first (to avoid double counting tranches)
company_industry = df.groupby(['bdc_name', 'company_name', 'industry_sector']).agg({
    'fair_value': 'sum',
    'principal': 'sum',
    'cost': 'sum',
}).reset_index()

# Then create industry-BDC detail
industry_detail = company_industry.groupby(['bdc_name', 'industry_sector']).agg({
    'company_name': 'count',
    'fair_value': 'sum',
    'principal': 'sum',
    'cost': 'sum',
}).rename(columns={'company_name': 'company_count'}).reset_index()

# Add totals for percentage calculations
bdc_totals = industry_detail.groupby('bdc_name').agg({
    'company_count': 'sum',
    'fair_value': 'sum',
}).reset_index()
bdc_totals.columns = ['bdc_name', 'total_companies', 'total_fair_value']

industry_detail = industry_detail.merge(bdc_totals, on='bdc_name')

# Calculate percentages
industry_detail['pct_companies'] = (industry_detail['company_count'] / industry_detail['total_companies'] * 100).round(2)
industry_detail['pct_fair_value'] = (industry_detail['fair_value'] / industry_detail['total_fair_value'] * 100).round(2)

# Add in millions
industry_detail['fair_value_millions'] = (industry_detail['fair_value'] / 1e6).round(2)
industry_detail['principal_millions'] = (industry_detail['principal'] / 1e6).round(2)
industry_detail['cost_millions'] = (industry_detail['cost'] / 1e6).round(2)

# Sort by BDC and fair value
industry_detail = industry_detail.sort_values(['bdc_name', 'fair_value'], ascending=[True, False])

# Reorder columns
industry_cols = [
    'bdc_name',
    'industry_sector',
    'company_count',
    'pct_companies',
    'fair_value_millions',
    'pct_fair_value',
    'principal_millions',
    'cost_millions',
    'fair_value',
    'principal',
    'cost',
    'total_companies',
    'total_fair_value',
]

output_path_industry = 'outputs/pivot_industry_bdc_detail.csv'
industry_detail[industry_cols].to_csv(output_path_industry, index=False)
print(f"✓ Created: {output_path_industry}")
print(f"  Rows: {len(industry_detail):,}")
print(f"  Columns: {len(industry_cols)}")
print(f"  Use for: Industry concentration analysis by BDC")

# ============================================================================
# Summary Report
# ============================================================================
print("\n" + "=" * 70)
print("DATA GENERATION COMPLETE")
print("=" * 70)

print("\nGenerated 5 entity-level CSV files for pivot analysis:")
print("\n1. pivot_investment_positions.csv")
print(f"   - {len(df_positions):,} rows (every investment position)")
print(f"   - Dimensions: BDC, Company, Industry, Investment Type, Overlap")
print(f"   - Values: Fair Value, Principal, Cost")
print(f"   - Use: Most granular analysis, multiple positions per company")

print("\n2. pivot_company_level.csv")
print(f"   - {len(company_agg):,} rows (one per company per BDC)")
print(f"   - Dimensions: BDC, Company, Industry, Overlap")
print(f"   - Values: Aggregated Fair Value, Principal, Cost, Position Count")
print(f"   - Use: Company-level analysis, avoids double-counting tranches")

print("\n3. pivot_unique_companies.csv")
print(f"   - {len(unique_companies):,} rows (one per unique company)")
print(f"   - Dimensions: Company, Industry, Holder Count, BDCs Holding")
print(f"   - Values: Total exposure across all BDCs")
print(f"   - Use: Cross-BDC analysis, identify shared holdings")

print("\n4. pivot_bdc_company_matrix.csv")
print(f"   - {len(bdc_company_matrix):,} rows (companies)")
print(f"   - Columns: One per BDC + Industry + Total + Holder Count")
print(f"   - Values: Fair value by BDC (millions)")
print(f"   - Use: Matrix/heatmap analysis, quick overlap identification")

print("\n5. pivot_industry_bdc_detail.csv")
print(f"   - {len(industry_detail):,} rows (industry × BDC combinations)")
print(f"   - Dimensions: BDC, Industry")
print(f"   - Values: Company count, Fair Value, Percentages")
print(f"   - Use: Industry concentration and diversification analysis")

# ============================================================================
# Create a data dictionary
# ============================================================================
print("\n" + "=" * 70)
print("CREATING DATA DICTIONARY")
print("=" * 70)

data_dict = pd.DataFrame({
    'File': [
        'pivot_investment_positions.csv',
        'pivot_investment_positions.csv',
        'pivot_investment_positions.csv',
        'pivot_investment_positions.csv',
        'pivot_investment_positions.csv',
        'pivot_investment_positions.csv',
        'pivot_investment_positions.csv',
        'pivot_investment_positions.csv',
        'pivot_investment_positions.csv',
        'pivot_investment_positions.csv',
        '',
        'pivot_company_level.csv',
        'pivot_company_level.csv',
        'pivot_company_level.csv',
        '',
        'pivot_unique_companies.csv',
        'pivot_unique_companies.csv',
        '',
        'pivot_bdc_company_matrix.csv',
        '',
        'pivot_industry_bdc_detail.csv',
        'pivot_industry_bdc_detail.csv',
    ],
    'Field': [
        'bdc_name',
        'company_name',
        'holder_count',
        'is_shared',
        'other_holders',
        'investment_type',
        'industry_sector',
        'fair_value_millions',
        'fair_value',
        'has_business_desc',
        '',
        'position_count',
        'total_exposure_across_bdcs',
        'industry_classified',
        '',
        'held_by_bdcs',
        'total_positions',
        '',
        'Holder_Count',
        '',
        'pct_companies',
        'pct_fair_value',
    ],
    'Description': [
        'Name of the BDC holding the investment',
        'Name of the portfolio company',
        'Number of BDCs holding this company (1-6)',
        'Boolean: True if held by multiple BDCs',
        'Comma-separated list of other BDCs holding this company',
        'Type of investment (Senior Debt, Equity, etc.)',
        'Classified industry sector (16 categories)',
        'Fair value in millions of dollars',
        'Fair value in raw dollars',
        'Boolean: True if business description exists',
        '',
        'Number of investment positions in this company',
        'Total fair value of this company across all BDCs (millions)',
        'Boolean: True if industry is not Unknown/Other',
        '',
        'Comma-separated list of BDCs holding this company',
        'Total number of positions across all BDCs',
        '',
        'Number of BDCs holding this company',
        '',
        'Percentage of BDC\'s companies in this industry',
        'Percentage of BDC\'s fair value in this industry',
    ]
})

output_path_dict = 'outputs/pivot_data_dictionary.csv'
data_dict.to_csv(output_path_dict, index=False)
print(f"✓ Created: {output_path_dict}")

print("\n" + "=" * 70)
print("SUGGESTED PIVOT TABLE ANALYSES")
print("=" * 70)

print("""
Using pivot_investment_positions.csv:
- BDC × Investment Type (sum of fair_value_millions)
- Industry × BDC × Investment Type (count or sum)
- Companies with is_shared = True

Using pivot_company_level.csv:
- BDC × Industry (count of companies, sum of fair_value_millions)
- Filter is_shared = True to see only overlapping companies
- Industry × Holder Count (identify concentrated sectors)

Using pivot_unique_companies.csv:
- Filter holder_count > 1 to see all shared companies
- Industry × Holder Count (sector overlap analysis)
- Sort by fair_value_millions to see largest exposures

Using pivot_bdc_company_matrix.csv:
- Create heatmap with company rows, BDC columns
- Conditional formatting to highlight overlaps
- Sort by Holder_Count to see most shared companies

Using pivot_industry_bdc_detail.csv:
- BDC × Industry with pct_fair_value
- Compare concentration across BDCs
- Identify BDC specializations
""")
