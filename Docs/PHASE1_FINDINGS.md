# Phase 1 Findings - BDC Data Profiling

**Date:** 2026-01-15
**Data Source:** SEC BDC Data Sets (2025_11_bdc.zip - November 2025)
**Status:** Phase 1 Complete - Data Profiling

---

## Key Findings

### Dataset Overview

- **Total investment records:** 132,282
- **Total columns:** 233 (XBRL tags as columns)
- **Data structure:** Pivoted XBRL format, not simple tabular format

### BDC Coverage

Only **4 of 10** target BDCs are present in the November 2025 data:

| CIK | Ticker | Name | Records |
|-----|--------|------|---------|
| 1476765 | GBDC | Golub Capital BDC, Inc. | 3,761 |
| 1396440 | MAIN | Main Street Capital Corp | 2,441 |
| 1496099 | NMFC | New Mountain Finance Corp | 1,642 |
| 1414932 | OCSL | Oaktree Specialty Lending Corp | 1,430 |

**Total:** 9,274 records from 4 BDCs

### Missing BDCs (Not in this dataset)

- ARCC (1287750) - Ares Capital Corporation
- FSK (1631115) - FS KKR Capital Corp
- BXSL (1838831) - Blackstone Secured Lending Fund
- ORCC (1758190) - Blue Owl Capital Corporation
- PSEC (1287032) - Prospect Capital Corporation
- HTGC (1280784) - Hercules Capital Inc

**Action Required:** These BDCs may have filed in different months. Need to check Q4 2024 (2024q4_bdc.zip) or other quarterly files.

---

## Portfolio Company Identification

### Available Identifiers

**NO traditional identifiers (CUSIP, LEI) found for portfolio companies.**

Available columns for portfolio company names:

| Column | Population | Coverage | Data Quality |
|--------|-----------|----------|--------------|
| `Investment, Identifier Axis` | 75.2% | **Best** | Company name + investment type combined |
| `Investment, Issuer Name Axis` | 4.5% | Limited | Clean company names |
| `Investment, Issuer Name [Extensible Enumeration]` | 1.8% | Poor | URL-based identifiers |

### Extraction Strategy

**Use hybrid approach:**

1. **Primary:** Extract company name from `Investment, Identifier Axis` (75% coverage)
   - Format: `"Company Name, LLC, Secured Debt 2"`
   - Strategy: Split on first comma, take company name
   - Example: `"AAC Holdings, Inc., Common Stock"` → `"AAC Holdings, Inc."`

2. **Secondary:** Use `Investment, Issuer Name Axis` directly when available (4.5%)
   - Format: `"Company Name [Member]"`
   - Strategy: Strip " [Member]" suffix
   - Example: `"AAC Holdings, Inc. [Member]"` → `"AAC Holdings, Inc."`

3. **Combined coverage:** ~79% of records will have portfolio company names

### Sample Portfolio Companies Found

From the 4 available BDCs, sample companies include:
- AAC Holdings, Inc.
- Adams Publishing Group, LLC
- Adelaide Borrower, LLC
- Bolder Panther Group, LLC
- Chamberlin Holding LLC
- Elgin AcquireCo, LLC
- Haven Midstream LLC
- National HME, Inc.
- Robbins Bros. Jewelry, Inc.
- UniTek Global Services, Inc.

---

## Data Structure Challenges

### Issue 1: XBRL Pivoted Format

The SOI data is NOT a simple table with rows = investments. Instead:
- Each row can represent different XBRL tag values
- Portfolio company info is spread across XBRL axis columns
- Not all investments have explicit company names in axis columns

### Issue 2: Low BDC Coverage

Only 4 of 10 target BDCs are in November 2025 file (9,274 records).

**Hypothesis:** Large BDCs like ARCC, FSK, BXSL may file annually (10-K) and appear in quarterly files.

**Recommendation:** Download and merge multiple periods:
- 2025_11_bdc.zip (current - 4 BDCs)
- 2025q1_bdc.zip (Q1 2025 - may have annual 10-K filings)
- 2024q4_bdc.zip (Q4 2024 - may have annual 10-K filings)

### Issue 3: Name Normalization Critical

Even with parsed names, we'll need aggressive normalization:
- Suffixes: LLC, Inc., Corp, Ltd, LP, L.P., L.L.C.
- Punctuation: commas, periods
- Case sensitivity
- Multiple entity references ("Company A And Company B And Company C")

---

## Recommendations for Phase 2

### Scenario C: Poor Identifier Coverage + Limited Data

**Given findings:**
- No CUSIP/LEI identifiers
- Only 4 of 10 BDCs in current file
- 75% coverage via parsed names

**Recommended matching strategy:**

1. **Download additional periods** to get all 10 BDCs
   - Try 2025q1_bdc.zip (Q1 2025)
   - Try 2024q4_bdc.zip (Q4 2024)
   - Merge datasets keeping most recent filing per BDC

2. **Extract portfolio company names**
   ```python
   def extract_company_name(row):
       # Try Investment, Issuer Name Axis first (cleanest)
       if pd.notna(row['Investment, Issuer Name Axis']):
           return row['Investment, Issuer Name Axis'].replace(' [Member]', '')

       # Parse from Investment, Identifier Axis (75% coverage)
       if pd.notna(row['Investment, Identifier Axis']):
           # Split on first comma, take company name
           parts = row['Investment, Identifier Axis'].split(',', 1)
           return parts[0].strip()

       return None
   ```

3. **Name normalization pipeline**
   - Lowercase
   - Remove punctuation
   - Standardize legal suffixes
   - Remove "and [company]" references
   - Fuzzy match threshold: 90+ for auto, 80-89 for manual review

4. **Match by exact normalized name first**
   - This should catch most true matches
   - Create entity master table with canonical names

5. **Fuzzy match remaining**
   - Use rapidfuzz token_set_ratio
   - Industry sector as secondary signal
   - Investment type as tertiary signal
   - Manual review for 80-90 similarity scores

---

## Alternative Approach: Direct EDGAR Parsing

If SEC BDC Data Sets prove too sparse or complex:

**Option:** Parse Schedule of Investments directly from 10-K/10-Q filings
- More complete data (100% of filings)
- More work to parse HTML/XBRL
- But guaranteed to have all portfolio company info

**Trade-off:** More engineering work vs better data quality

---

## Next Steps

### Immediate Actions

1. **Download additional periods**
   ```bash
   python3 -m src.download --period=2025q1
   python3 -m src.download --period=2024q4
   ```

2. **Check BDC coverage in each file**
   - Identify which periods contain which BDCs
   - Map out filing patterns

3. **Decide on approach:**
   - **Option A:** Continue with SEC BDC Data Sets (current path)
     - Need to merge multiple periods
     - Name parsing and normalization required

   - **Option B:** Switch to direct EDGAR parsing
     - More complete data
     - More engineering work
     - Guaranteed coverage of all 10 BDCs

### Phase 2 Implementation (if continuing with SEC data)

1. Update load.py to:
   - Load multiple period files
   - Merge keeping most recent per BDC
   - Extract portfolio company names using hybrid strategy

2. Create normalize.py with:
   - Company name parser
   - Name normalization function
   - Exact match first pass
   - Fuzzy match second pass

3. Implement overlap analysis with normalized names

4. Generate overlap matrix and Excel output

---

## Files Generated

- ✅ `src/download.py` - Updated with correct SEC URLs
- ✅ `src/load.py` - Loads SOI and submission data
- ✅ `src/profile.py` - Data profiling and analysis
- ✅ `src/overlap.py` - Overlap calculation logic
- ✅ `src/export.py` - Excel export with formatting
- ✅ `Docs/DATA_PROFILE.md` - Detailed column analysis
- ✅ `Docs/PHASE1_FINDINGS.md` - This document
- ✅ `Docs/PLANNING.md` - Updated with correct SEC URLs

---

## Question for Decision

**Should we proceed with SEC BDC Data Sets approach, or switch to direct EDGAR parsing?**

**SEC BDC Data Sets (current):**
- ✅ Pre-extracted by SEC
- ✅ Consistent structure
- ❌ Only 4/10 BDCs in November file
- ❌ Complex XBRL pivoted format
- ❌ Need to parse company names
- ❌ No CUSIP/LEI identifiers

**Direct EDGAR Parsing:**
- ✅ Complete coverage (all BDCs, all filings)
- ✅ Full Schedule of Investments data
- ✅ Likely has company identifiers in some filings
- ❌ More engineering work to parse HTML/XBRL
- ❌ Inconsistent formatting across BDCs
- ❌ Need to handle different filing formats
