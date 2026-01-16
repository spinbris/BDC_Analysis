# BDC Portfolio Overlap Analysis - Implementation Summary

## Overview

Successfully implemented Phase 2 of the BDC Portfolio Overlap Analysis using direct EDGAR HTML parsing via the EdgarTools library. Achieved 60% BDC coverage (6 of 10 target BDCs) with 3,410 investment positions extracted representing $136.53B in fair value.

## Implementation Approach

### Data Source Selection

**Initial Approach (Phase 1):**
- SEC BDC Data Sets (pre-extracted XBRL data)
- **Issues Found:**
  - Only 4 of 10 target BDCs present in dataset
  - No entity identifiers (CUSIP, LEI) for portfolio companies
  - 75% of company names embedded in complex XBRL dimension fields
  - Complex pivoted structure (233 columns)

**Final Approach (Phase 2):**
- Direct EDGAR 10-K HTML parsing using EdgarTools
- **Advantages:**
  - 8-10 of 10 BDCs accessible (vs 4/10 in datasets)
  - Clean, explicit company names in HTML tables
  - No entity resolution needed for initial analysis
  - More recent data (filings from Feb-Mar 2025)

### Parser Development

Built `src/edgar_parser.py` with the following key functions:

1. **`get_bdc_10k(ticker_or_cik)`** - Retrieve latest 10-K filing
2. **`parse_schedule_of_investments(filing)`** - Main parsing orchestrator
3. **`extract_holdings_from_table(table_html)`** - Extract holdings from individual tables
4. **`parse_dollar_amount(value)`** - Parse various dollar formats
5. **`clean_company_name(name)`** - Standardize company names

## Major Challenges and Solutions

### Challenge 1: Wrong CIK Numbers

**Problem:** Initial CIK mapping for FSK, ORCC, and BXSL were incorrect, causing "index out of bounds" errors.

**Investigation:**
- Created `src/investigate_missing_bdcs.py` to search by ticker
- Found BDCs filed under different CIKs than initially mapped

**Solution:**
Updated `TOP_10_BDCS` mapping:
- FSK: 1422183 (was 1631115)
- ORCC: 1655888 (was 1758190)
- BXSL: 1736035 (was 1838831)

### Challenge 2: Initial Parser Extracted Zero Holdings

**Problem:** Parser found candidate tables but extracted 0 holdings from all of them.

**Investigation:**
1. Saved sample ARCC table to HTML file
2. Used pandas.read_html() to examine structure
3. Found DataFrame shape: (25, 66) - columns repeated 3x due to HTML colspan
4. Discovered headers in row 1 (not row 0)
5. Found values in millions (6.6 = $6.6M, not $6.60)

**Root Causes:**
- Header detection looked at row 0 only
- Column detection took all occurrences (got repeated columns)
- Value scaling was incorrect

**Solution:**
```python
# Search rows 0-2 for header row
for i in range(min(3, len(df))):
    row_text = ' '.join([str(v).lower() for v in df.iloc[i].values if pd.notna(v)])
    if 'company' in row_text and 'fair value' in row_text:
        header_row_idx = i
        break

# Take FIRST occurrence of each column (due to colspan repeats)
if 'company' in header_str and company_col is None:
    company_col = i
```

### Challenge 3: Different Table Formats - MAIN (Multi-Row)

**Problem:** MAIN tables structured differently - company name in one row, investment details in subsequent rows without repeating the name.

**Example:**
```
Row 7: "Analytical Systems Keco, LLC" | Business Desc | (empty investment fields)
Row 8: (empty company) | (empty) | Secured Debt | $4,095 | $4,048 | $4,048
Row 9: (empty company) | (empty) | Preferred Units | $2,427 | $5,300
```

**Solution:**
Implemented stateful parsing with `current_company` and `current_business_desc` variables:
```python
current_company = None
current_business_desc = None

for idx in range(header_row_idx + 1, len(df)):
    # If row has company name, update current_company
    if row_company_name and len(row_company_name) >= 3:
        current_company = clean_company_name(row_company_name)
        current_business_desc = ...

    # Extract investment data from this row
    # Use current_company (might be from previous row)
    if current_company and has_values:
        holdings.append({...})
```

### Challenge 4: Inconsistent Value Scales (Thousands vs Millions)

**Problem:** Different BDCs use different scales:
- ARCC: Values in millions (6.6 = $6.6M)
- MAIN: Values in thousands (4,048 = $4,048K)

Initial fix (multiply values < 1000 by 1M) broke ARCC when fixing MAIN.

**Solution:**
Auto-detect scale for each table by sampling values:
```python
# Sample first 50 data rows
sample_values = []
for idx in range(header_row_idx + 1, min(header_row_idx + 50, len(df))):
    for col in [fair_value_col, cost_col, principal_col]:
        val = parse_dollar_amount(row.iloc[col])
        if val and val > 0:
            sample_values.append(val)

# Determine multiplier based on median
median_val = sorted(sample_values)[len(sample_values) // 2]
if median_val < 1000:
    value_multiplier = 1_000_000  # Values in millions
else:
    value_multiplier = 1_000  # Values in thousands
```

### Challenge 5: FSK Tables Without Investment Type Column

**Problem:** FSK tables don't have "Type of Investment" column. Parser required `investment_type` to be non-None to create holdings.

**FSK Table Structure:**
```
Portfolio Company | Footnotes | Industry | Rate | Floor | Maturity | Principal | Cost | Fair Value
```

**Solution:**
Made investment_type optional:
```python
# OLD: Required investment_type
if current_company and investment_type and has_values:

# NEW: investment_type is optional
if current_company and has_values:
    holdings.append({
        'investment_type': investment_type,  # Can be None
        ...
    })
```

## Results Achieved

### Successfully Parsed BDCs (6 of 10)

| BDC | Ticker | Holdings | Fair Value |
|-----|--------|----------|------------|
| FS KKR Capital Corp | FSK | 812 | $56.34B |
| Ares Capital Corporation | ARCC | 768 | $33.17B |
| Prospect Capital Corporation | PSEC | 572 | $30.50B |
| Main Street Capital Corporation | MAIN | 649 | $9.37B |
| New Mountain Finance Corporation | NMFC | 560 | $6.53B |
| Oaktree Specialty Lending Corporation | OCSL | 49 | $0.62B |
| **TOTAL** | | **3,410** | **$136.53B** |

### Failed to Parse BDCs (4 of 10)

The following BDCs still need investigation:

1. **BXSL (Blackstone Secured Lending Fund)**
   - Tables found (11-30 candidates per run)
   - Header detection failing
   - Likely different table structure

2. **ORCC (Blue Owl Capital Corp)**
   - Tables found (29 candidates)
   - Header detection failing
   - Likely different table structure

3. **GBDC (Golub Capital BDC Inc)**
   - Tables found (29 candidates)
   - Header detection failing
   - Likely different table structure

4. **HTGC (Hercules Capital Inc)**
   - Tables found (29 candidates)
   - Header detection failing
   - Likely different table structure

**Pattern:** All 4 failing BDCs find candidate tables but fail header detection. The current logic looks for a row containing both "company" and "fair value" text, which may not match these BDCs' header formats.

## Remaining Issues

### 1. 4 BDCs Not Parsing (40% failure rate)

**Hypothesis:**
- Different header text (e.g., "Portfolio Company" vs "Borrower" vs "Investment")
- Different table organization (multi-level headers, section groupings)
- Tables split across multiple pages/sections

**Next Steps:**
1. Run debug script on one failing BDC (e.g., GBDC)
2. Examine actual table HTML structure
3. Compare with successful BDC table structure
4. Adjust header detection logic to handle variations
5. Test fix and apply to remaining 3 BDCs

### 2. Company Name Matching Only

**Current:** Exact string matching on company names

**Limitations:**
- Name variations (e.g., "ABC Corp" vs "ABC Corporation" vs "ABC, Inc.")
- Typos or formatting differences
- Subsidiary vs parent company names
- May undercount actual overlaps

**Future Enhancement:**
- Fuzzy string matching (Levenshtein distance)
- Entity resolution using business identifiers (EIN, DUNS)
- Name normalization/canonicalization

### 3. Multiple Investment Positions Per Company

**Observation:** Average 4.1 investments per company

**Explanation:**
- Same company may have multiple investment types (Senior Debt, Junior Debt, Equity)
- Multiple tranches with different maturities
- Secured vs unsecured positions

**Current Handling:** Each position treated as separate record

**Future Enhancement:**
- Aggregate by company to get total exposure per BDC
- Separate analysis by investment type
- Visualize capital structure (debt vs equity)

### 4. Missing Entity Identifiers

**Issue:** No CUSIP, LEI, or other standard identifiers in parsed data

**Impact:** Cannot easily link to external databases or validate company matches

**Workaround:** Using company names as primary identifier

### 5. Data Freshness

**Current:** Using latest 10-K filings (Feb-Mar 2025)

**Limitation:** 10-K filed once per year - portfolio holdings may have changed

**Alternative:** Could parse quarterly 10-Q filings for more recent data (but more filings to process)

## Code Structure

```
src/
├── edgar_parser.py          # Main parser module
├── test_all_bdcs.py         # Test parser on all 10 BDCs
├── overlap.py               # Overlap analysis functions
├── analyze_overlap.py       # Run overlap analysis
├── export.py                # Excel export utilities
├── generate_report.py       # Generate final Excel report
└── debug_*.py              # Debug scripts for investigating issues

outputs/
├── all_bdc_holdings.csv           # Combined holdings (3,410 rows)
├── common_holdings_2plus.csv      # Shared companies (1 row)
├── bdc_overlap_matrix.csv         # BDC x BDC overlap
├── bdc_overlap_summary.csv        # Per-BDC statistics
└── bdc_overlap_analysis.xlsx      # Final Excel report (6 tabs)
```

## Key Learnings

1. **Direct HTML parsing > pre-processed datasets** when data coverage is critical
2. **Auto-detection is essential** when dealing with heterogeneous data formats
3. **Stateful parsing** needed for multi-row table formats
4. **Defensive programming** - check multiple rows for headers, handle missing columns
5. **Iterative debugging** - save sample data, examine structure, test fixes incrementally

## Time Investment

- Initial SEC dataset investigation: 30 minutes
- EdgarTools spike test: 30 minutes
- Parser development: 3-4 hours (including debugging)
- Overlap analysis: 30 minutes
- Report generation: 30 minutes
- **Total: ~6 hours**

## Success Metrics

✅ **60% BDC coverage** (6 of 10 target BDCs)
✅ **$136.53B portfolio value** extracted
✅ **3,410 investment positions** parsed
✅ **Overlap analysis completed** (0.1% concentration rate)
✅ **Excel report generated** with 6 comprehensive tabs
⚠️ **4 BDCs remain unparsed** (requires further investigation)
