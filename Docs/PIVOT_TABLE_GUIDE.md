# BDC Portfolio Analysis - Pivot Table Guide

## Overview

This guide explains how to use the 5 entity-level CSV files for detailed pivot table analysis in Excel, Tableau, or other BI tools. All files include overlap and industry information at the most granular level possible.

## Files Generated

All files located in `outputs/` directory:

1. **pivot_investment_positions.csv** (3,410 rows) - Most granular
2. **pivot_company_level.csv** (832 rows) - Aggregated by company per BDC
3. **pivot_unique_companies.csv** (831 rows) - One row per unique company
4. **pivot_bdc_company_matrix.csv** (831 rows) - Matrix format
5. **pivot_industry_bdc_detail.csv** (34 rows) - Industry summary
6. **pivot_data_dictionary.csv** - Field definitions

## File Descriptions

### File 1: Investment Positions (Most Detailed)

**pivot_investment_positions.csv** - 3,410 rows

**Purpose:** Most granular view - every individual investment position

**Key Fields:**
- `bdc_name` - Name of BDC holding the investment
- `company_name` - Portfolio company name
- `holder_count` - Number of BDCs holding this company (1-6)
- `is_shared` - TRUE if held by multiple BDCs
- `other_holders` - Comma-separated list of other BDCs
- `investment_type` - Type (Senior Debt, Equity, etc.)
- `industry_sector` - Classified industry (16 categories)
- `fair_value_millions` - Fair value in $M
- `has_business_desc` - TRUE if description exists
- `industry_classified` - TRUE if not Unknown/Other

**Use Cases:**
- Analyze by investment type (debt vs equity)
- Count number of positions per company
- Detailed drill-down into specific investments
- Multiple tranches/positions per company visible

**Excel Pivot Table Examples:**

```
ROWS: bdc_name, investment_type
COLUMNS: industry_sector
VALUES: Sum of fair_value_millions
```

```
ROWS: company_name
COLUMNS: bdc_name
VALUES: Count of investment_type
FILTERS: is_shared = TRUE
```

### File 2: Company Level (Recommended for Most Analysis)

**pivot_company_level.csv** - 832 rows

**Purpose:** One row per company per BDC (aggregated positions)

**Key Fields:**
- `bdc_name` - BDC name
- `company_name` - Company name
- `holder_count` - Number of BDCs holding this company
- `is_shared` - TRUE if multiple BDCs hold it
- `other_holders` - Which other BDCs hold it
- `industry_sector` - Industry classification
- `position_count` - Number of positions in this company
- `investment_type` - All investment types (comma-separated)
- `fair_value_millions` - Total exposure to this company
- `total_exposure_across_bdcs` - Company's total across ALL BDCs

**Use Cases:**
- Company-level exposure analysis
- Avoid double-counting multiple tranches
- Industry concentration analysis
- Cross-BDC comparison at company level

**Excel Pivot Table Examples:**

```
ROWS: bdc_name
COLUMNS: industry_sector
VALUES: Count of company_name
```

```
ROWS: bdc_name, industry_sector
VALUES: Sum of fair_value_millions, Count of company_name
FILTERS: holder_count > 1 (to see only shared companies)
```

```
ROWS: company_name, industry_sector
COLUMNS: bdc_name
VALUES: Sum of fair_value_millions
SORT: By total_exposure_across_bdcs descending
```

### File 3: Unique Companies (Cross-BDC View)

**pivot_unique_companies.csv** - 831 rows

**Purpose:** One row per unique company across all BDCs

**Key Fields:**
- `company_name` - Company name
- `holder_count` - Number of BDCs holding (1-6)
- `is_shared` - TRUE if held by multiple BDCs
- `held_by_bdcs` - Comma-separated list of BDCs
- `industry_sector` - Industry classification
- `total_positions` - Total positions across all BDCs
- `fair_value_millions` - Total fair value across all BDCs

**Use Cases:**
- Identify all shared holdings
- Analyze companies by number of holders
- Find largest cross-BDC exposures
- Industry overlap analysis

**Excel Pivot Table Examples:**

```
ROWS: industry_sector, company_name
VALUES: Sum of fair_value_millions
FILTERS: is_shared = TRUE
```

```
ROWS: holder_count, industry_sector
VALUES: Count of company_name, Sum of fair_value_millions
```

**Filtering Examples:**
- Filter `holder_count = 2` to see companies held by exactly 2 BDCs
- Filter `is_shared = TRUE` to see only overlapping companies
- Sort by `fair_value_millions` descending to see largest exposures

### File 4: BDC-Company Matrix (Quick Analysis)

**pivot_bdc_company_matrix.csv** - 831 rows × 9 columns

**Purpose:** Pre-pivoted matrix with companies as rows, BDCs as columns

**Structure:**
- Row: Each unique company
- Columns: One column per BDC (6 total)
- Values: Fair value in millions ($0 if not held)
- Additional columns: Industry, Total, Holder_Count

**Use Cases:**
- Heatmap visualization
- Quick identification of overlaps
- Sort/filter by holder count
- Matrix-style comparison

**Excel Usage:**

1. **Conditional Formatting:**
   - Select BDC columns (columns C-H)
   - Apply color scale (green = high, white = 0)
   - Instantly see which companies each BDC holds

2. **Filter for Overlaps:**
   - Filter `Holder_Count > 1`
   - Shows only companies held by multiple BDCs

3. **Sort by Total:**
   - Sort by `Total` column descending
   - See companies with largest total exposure

**Creating Heatmap in Excel:**
```
1. Select data range (columns C-H with BDC values)
2. Home > Conditional Formatting > Color Scales
3. Choose Green-Yellow-Red scale
4. Red = 0, Green = highest values
5. Overlaps will show multiple colored cells in same row
```

### File 5: Industry-BDC Detail (Summary Level)

**pivot_industry_bdc_detail.csv** - 34 rows

**Purpose:** Pre-aggregated industry × BDC summary statistics

**Key Fields:**
- `bdc_name` - BDC name
- `industry_sector` - Industry
- `company_count` - Number of companies
- `pct_companies` - % of BDC's companies
- `fair_value_millions` - Fair value ($M)
- `pct_fair_value` - % of BDC's portfolio

**Use Cases:**
- Industry concentration analysis
- BDC strategy comparison
- Concentration metrics (HHI)
- Quick summary views

**Excel Pivot Table Examples:**

```
ROWS: bdc_name
COLUMNS: industry_sector
VALUES: Sum of pct_fair_value
```

```
ROWS: industry_sector
COLUMNS: bdc_name
VALUES: Sum of company_count
```

## Common Pivot Table Analyses

### Analysis 1: BDC Portfolio Composition

**Goal:** See each BDC's holdings by industry

**File:** `pivot_company_level.csv`

**Pivot Setup:**
- Rows: `bdc_name`, `industry_sector`
- Values:
  - Count of `company_name`
  - Sum of `fair_value_millions`
- Sort: By sum of fair_value_millions descending

**Insight:** Shows industry concentration for each BDC

### Analysis 2: Shared Holdings

**Goal:** Find all companies held by multiple BDCs

**File:** `pivot_unique_companies.csv`

**Filter:** `is_shared = TRUE` OR `holder_count > 1`

**Columns to Show:**
- `company_name`
- `holder_count`
- `held_by_bdcs`
- `industry_sector`
- `fair_value_millions`

**Sort:** By `fair_value_millions` descending

**Insight:** Identifies concentration risk at company level

### Analysis 3: Industry Overlap

**Goal:** Which industries have the most overlap?

**File:** `pivot_company_level.csv`

**Pivot Setup:**
- Rows: `industry_sector`
- Columns: `holder_count`
- Values: Count of `company_name`
- Filter: `holder_count > 1`

**Insight:** Shows which sectors have shared companies

### Analysis 4: Investment Type Distribution

**Goal:** Debt vs Equity by BDC

**File:** `pivot_investment_positions.csv`

**Pivot Setup:**
- Rows: `bdc_name`, `investment_type`
- Values:
  - Count of records
  - Sum of `fair_value_millions`

**Insight:** Shows capital structure preferences

### Analysis 5: Industry Concentration by BDC

**Goal:** Calculate concentration metrics

**File:** `pivot_industry_bdc_detail.csv`

**Already Calculated:**
- `pct_fair_value` shows % of portfolio in each industry
- `pct_companies` shows % of companies in each industry

**Pivot Setup:**
- Rows: `bdc_name`
- Columns: `industry_sector`
- Values: `pct_fair_value`

**Sort industries by total across BDCs**

**Insight:** Identifies concentrated vs diversified portfolios

### Analysis 6: Largest Exposures

**Goal:** Find biggest investments across all BDCs

**File:** `pivot_company_level.csv`

**Sort:** By `fair_value_millions` descending

**Show Top 50**

**Group by:** `industry_sector` to see which sectors dominate

**Insight:** Identifies tail risk (large exposures)

### Analysis 7: BDC Strategy Comparison

**Goal:** Compare 2 BDCs side-by-side

**File:** `pivot_bdc_company_matrix.csv`

**Example:** ARCC vs MAIN

**Filter:**
- `Ares Capital Corporation > 0` OR `Main Street Capital Corporation > 0`

**Columns to show:**
- `company_name`
- `Industry`
- `Ares Capital Corporation`
- `Main Street Capital Corporation`
- `Holder_Count`

**Conditional Format:** Highlight rows where both have values > 0

**Insight:** Shows overlap and differentiation

## Advanced Excel Techniques

### Creating a Dynamic Dashboard

1. **Import all CSV files** into Excel as separate sheets

2. **Create a Dashboard sheet** with:
   - Slicers for: BDC, Industry, Is_Shared
   - Pivot charts showing:
     - Portfolio composition by BDC
     - Industry distribution
     - Shared companies count
   - Key metrics (calculated):
     - Total unique companies
     - Total shared companies
     - Concentration %

3. **Link Slicers** to all pivot tables for interactive filtering

### Power Query for Data Refresh

1. **Load CSVs via Power Query** instead of manual import
2. **Create relationships** between tables:
   - company_name as key
   - Link positions → companies → unique companies
3. **Refresh button** updates all tables when CSVs change

### Conditional Formatting Patterns

**Highlight Shared Companies:**
```
Formula: =AND($D2>1)  (if holder_count column is D)
Format: Yellow fill
```

**Highlight Large Exposures:**
```
Formula: =$J2>100  (if fair_value_millions column is J)
Format: Red text, bold
```

**Heatmap for BDC Matrix:**
```
Select BDC value columns
Conditional Formatting > Color Scales
Use: Green (high) to White (zero)
```

## Tips for Different Tools

### Microsoft Excel

- **Recommended File:** pivot_company_level.csv (avoids double-counting)
- **Pivot Tables:** Insert > PivotTable > Use entire dataset
- **Slicers:** PivotTable Analyze > Insert Slicer (filter by BDC, Industry)
- **Charts:** Insert > PivotChart based on pivot table
- **Power Pivot:** For very large datasets or complex calculations

### Google Sheets

- **Import:** File > Import > Upload CSV
- **Pivot Tables:** Data > Pivot table
- **Filters:** Use Filter views for different analyses
- **Sharing:** Share with collaborators for real-time analysis

### Tableau

1. **Connect to Data:** Connect > Text file > Select CSVs
2. **Relationships:**
   - Join on `company_name`
   - Link positions → company level → unique companies
3. **Create Visualizations:**
   - Treemap: BDC size by Industry
   - Heatmap: Company × BDC matrix
   - Bar chart: Shared companies by industry
4. **Dashboard:** Combine multiple visualizations with filters

### Python (Pandas)

```python
import pandas as pd

# Load data
positions = pd.read_csv('outputs/pivot_investment_positions.csv')
companies = pd.read_csv('outputs/pivot_company_level.csv')

# Find shared holdings
shared = companies[companies['is_shared'] == True]

# Industry concentration
industry_conc = companies.groupby(['bdc_name', 'industry_sector']).agg({
    'company_name': 'count',
    'fair_value_millions': 'sum'
})

# Create pivot
matrix = companies.pivot_table(
    index='company_name',
    columns='bdc_name',
    values='fair_value_millions',
    fill_value=0
)
```

### R

```r
library(tidyverse)

# Load data
positions <- read_csv('outputs/pivot_investment_positions.csv')
companies <- read_csv('outputs/pivot_company_level.csv')

# Find shared holdings
shared <- companies %>% filter(is_shared == TRUE)

# Industry concentration
industry_conc <- companies %>%
  group_by(bdc_name, industry_sector) %>%
  summarise(
    company_count = n(),
    total_fv = sum(fair_value_millions)
  )

# Create matrix
matrix <- companies %>%
  pivot_wider(
    names_from = bdc_name,
    values_from = fair_value_millions,
    values_fill = 0
  )
```

## Example Questions You Can Answer

### Portfolio Overlap

1. **How many companies are shared between BDCs?**
   - File: pivot_unique_companies.csv
   - Filter: is_shared = TRUE
   - Answer: Count of rows

2. **Which BDC pairs have the most overlap?**
   - File: pivot_bdc_company_matrix.csv
   - For each BDC pair, count rows where both > 0

3. **What is the overlap rate by industry?**
   - File: pivot_company_level.csv
   - Group by industry_sector
   - Calculate: shared companies / total companies

### Industry Concentration

1. **What % of each BDC's portfolio is in tech?**
   - File: pivot_industry_bdc_detail.csv
   - Filter: industry_sector = 'Software/Technology'
   - Show: pct_fair_value by bdc_name

2. **Which BDC is most diversified?**
   - File: pivot_industry_bdc_detail.csv
   - Calculate Herfindahl-Hirschman Index (HHI)
   - Or: Count industries with > 5% allocation

3. **Are there any industries with no overlap?**
   - File: pivot_company_level.csv
   - Group by industry_sector
   - Filter: Max(holder_count) = 1

### Investment Strategy

1. **What types of investments does each BDC prefer?**
   - File: pivot_investment_positions.csv
   - Pivot: bdc_name × investment_type
   - Values: Count or Sum of fair_value_millions

2. **Which BDC has the most positions per company?**
   - File: pivot_company_level.csv
   - Average position_count by bdc_name

3. **What's the average investment size by BDC?**
   - File: pivot_company_level.csv
   - Average fair_value_millions by bdc_name

### Risk Analysis

1. **What's the largest single company exposure?**
   - File: pivot_unique_companies.csv
   - Sort by fair_value_millions descending
   - Top row

2. **Which companies appear in the most BDCs?**
   - File: pivot_unique_companies.csv
   - Sort by holder_count descending

3. **What % of portfolio is shared vs unique?**
   - File: pivot_company_level.csv
   - Sum fair_value_millions where is_shared = TRUE / Total

## Data Refresh Process

When new data is available:

1. **Re-run parser:** `python -m src.test_all_bdcs`
2. **Classify industries:** `python -m src.classify_industries`
3. **Generate entity files:** `python -m src.generate_entity_level_data`
4. **Refresh Excel:** Power Query > Refresh All
5. **All pivots update automatically**

## Troubleshooting

### Issue: Pivot table shows wrong totals

**Cause:** Using pivot_investment_positions.csv with multiple positions per company

**Solution:** Use pivot_company_level.csv instead to aggregate positions first

### Issue: Can't find shared companies

**Cause:** holder_count column not filtered

**Solution:** Add filter: holder_count > 1 OR is_shared = TRUE

### Issue: Industry showing as "Unknown"

**Cause:** BDC doesn't have business_description field

**Solution:** Filter has_business_desc = TRUE for analysis

### Issue: Values seem too large or too small

**Cause:** Using wrong column (fair_value vs fair_value_millions)

**Solution:** Use *_millions columns for readable numbers

## Summary

**For most analysis, use:**
- **pivot_company_level.csv** - Best balance of detail and aggregation
- **pivot_unique_companies.csv** - For cross-BDC comparison

**For specific needs:**
- **pivot_investment_positions.csv** - Investment type analysis
- **pivot_bdc_company_matrix.csv** - Quick heatmap/matrix views
- **pivot_industry_bdc_detail.csv** - Pre-calculated summaries

**Key fields for filtering:**
- `is_shared` - Find overlapping companies
- `holder_count` - Number of BDCs holding
- `industry_sector` - Industry analysis
- `has_business_desc` - Data quality flag

All files include the same core dimensions (BDC, Company, Industry, Overlap) so you can switch between them based on the level of detail needed.
