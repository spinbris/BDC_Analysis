# EdgarTools Spike Test Results

**Date:** 2026-01-16
**Purpose:** Evaluate direct EDGAR parsing vs SEC BDC Data Sets approach
**Status:** Spike Complete - Findings Below

---

## Test Results Summary

### ✅ Filing Accessibility

**8 of 10 target BDCs** have accessible 10-K filings via edgartools:

| Ticker | CIK | Accessible | Latest Filing Date |
|--------|-----|------------|-------------------|
| ARCC | 1287750 | ✅ | 2025-02-05 (10-K) |
| FSK | 1631115 | ❌ | No recent 10-K found |
| BXSL | 1838831 | ✅ | 2023-04-17 (10-K) |
| ORCC | 1758190 | ❌ | No recent 10-K found |
| GBDC | 1476765 | ✅ | 2025-11-18 (10-K) |
| PSEC | 1287032 | ✅ | 2025-08-26 (10-K) |
| MAIN | 1396440 | ✅ | 2025-02-28 (10-K) |
| HTGC | 1280784 | ✅ | 2025-02-13 (10-K) |
| NMFC | 1496099 | ✅ | 2025-02-26 (10-K) |
| OCSL | 1414932 | ✅ | 2025-11-18 (10-K) |

**Note:** BXSL filing is from 2023 (ticker change from SPAC?), needs investigation.

---

## Schedule of Investments Extraction

### ✅ Successful Findings

**1. HTML Structure is Parseable**
- Schedule of Investments found at character position 4,742,850 in ARCC 10-K (22.5MB HTML)
- Multiple tables present (20+ tables in SOI section)
- Tables are well-structured HTML with proper `<table>`, `<tr>`, `<td>` tags

**2. Portfolio Company Data is Clear**

Sample companies extracted from ARCC Schedule of Investments:
- Regent Education, Inc.
- Relativity ODA LLC
- Revalize, Inc.
- RMS HoldCo II, LLC & RMS Group Holdings, Inc.
- Runway Bidco, LLC
- Sapphire Software Buyer, Inc.
- Severin Acquisition, LLC
- Smarsh Inc. and Skywalker TopCo, LLC
- SocialFlow, Inc.
- SoundCloud Limited

**3. Data Fields Present**

Each investment record includes:
- Company name (clean, explicit)
- Business description
- Investment type (loan, warrant, equity)
- Coupon/interest rate
- Maturity date
- Principal amount
- Amortized cost
- Fair value
- % of net assets

**4. Table Structure**

- Tables are organized by industry sector (Software, Healthcare, etc.)
- Each industry has its own table (20+ tables total for full SOI)
- Each table: ~25-33 rows, ~66 columns
- Total portfolio likely 400-600+ companies across all tables

---

## Comparison: EdgarTools vs SEC BDC Data Sets

### EdgarTools Approach (Direct EDGAR Parsing)

**Pros:**
- ✅ Company names are explicit and clean
- ✅ Business descriptions available
- ✅ All data fields clearly labeled
- ✅ 8 of 10 BDCs accessible
- ✅ HTML structure is consistent and parseable
- ✅ Full historical data available (any quarter/year)
- ✅ Can use edgartools library for downloading
- ✅ No identifier matching needed - names are clean

**Cons:**
- ❌ Need to parse HTML tables (but BeautifulSoup/pandas work well)
- ❌ Multiple tables per filing (need to merge ~20 tables)
- ❌ Some complexity in table parsing (66 columns, some multi-row)
- ❌ Two BDCs (FSK, ORCC) not immediately accessible

**Engineering Effort:** Medium
- HTML parsing with pandas.read_html() works
- Need to iterate through multiple tables
- Need to handle multi-row investments (same company, different loan tranches)
- Estimated: 1-2 days to build robust parser

---

### SEC BDC Data Sets Approach (Current)

**Pros:**
- ✅ Pre-extracted by SEC (no HTML parsing)
- ✅ Consistent TSV format
- ✅ Already downloaded and profiled

**Cons:**
- ❌ Only 4 of 10 BDCs in November 2025 file
- ❌ Need to merge multiple period files
- ❌ Complex XBRL pivoted structure (233 columns)
- ❌ No explicit company names - must parse from composite fields
- ❌ Only 75% coverage via `Investment, Identifier Axis` parsing
- ❌ No CUSIP/LEI identifiers
- ❌ Requires name normalization and fuzzy matching
- ❌ Lower confidence in entity matching

**Engineering Effort:** Medium-High
- Already have 4 BDCs profiled
- Need to download additional periods
- Need to build name parser
- Need to build name normalization pipeline
- Need fuzzy matching with manual review
- Estimated: 2-3 days for full entity resolution

---

## XBRL vs HTML

**XBRL Data (via edgartools):**
- ❌ Only contains standard financial statements
- ❌ Does NOT include Schedule of Investments details
- ❌ Not useful for our purpose

**HTML Data:**
- ✅ Contains full Schedule of Investments
- ✅ Well-structured tables
- ✅ Easily parseable with pandas.read_html()
- ✅ This is the way to go

---

## Recommendation

### **Switch to EdgarTools (Direct EDGAR Parsing)**

**Rationale:**

1. **Better Data Quality**
   - Clean company names (no parsing needed)
   - Full investment details
   - Business descriptions included

2. **Better Coverage**
   - 8 of 10 BDCs accessible immediately
   - Can get FSK/ORCC with more investigation
   - Full historical data available

3. **Lower Risk**
   - No entity resolution/fuzzy matching needed
   - Explicit company names eliminate matching errors
   - Can validate against SEC website directly

4. **Similar Effort**
   - HTML parsing: 1-2 days
   - SEC Data Sets entity resolution: 2-3 days
   - EdgarTools approach is actually LESS work

5. **Future Proof**
   - Can easily add more BDCs
   - Can pull any historical period
   - Full control over data extraction

---

## Implementation Plan (If Approved)

### Phase 2 (Revised): Direct EDGAR Parsing

**Tasks:**

1. **Create `src/edgar_parser.py`**
   - Function to extract all SOI tables from a 10-K filing
   - Merge multiple industry tables into single DataFrame
   - Clean column names
   - Handle multi-row investments (same company, different tranches)

2. **Update `src/download.py`** (or create new module)
   - Use edgartools to fetch 10-K filings for target BDCs
   - Cache filings locally
   - Extract HTML content

3. **Create `src/parser_test.py`**
   - Test parser on all 8 accessible BDCs
   - Validate company name extraction
   - Validate fair value extraction
   - Generate quality report

4. **Build overlap analysis**
   - Use exact company name matching (no normalization needed initially)
   - See how many matches we get
   - Then decide if name normalization is needed

5. **Export results**
   - Use existing export.py
   - Generate Excel with all BDC holdings and overlap

**Timeline:** 2-3 days for full implementation

---

## Outstanding Questions

1. **Why are FSK and ORCC not accessible?**
   - Different ticker symbols?
   - Recently merged/renamed?
   - Filing under different form type?
   - Action: Manual SEC EDGAR search

2. **BXSL filing from 2023**
   - Company changed from SPAC structure?
   - Need more recent filing?
   - Action: Check if there are 10-Q filings

3. **How to handle multi-tranche loans?**
   - Same company, multiple first lien loans
   - Should we aggregate or keep separate?
   - Likely aggregate for overlap analysis

---

## Files Created

- ✅ `src/spike_edgartools.py` - Spike test script
- ✅ `outputs/target_bdc_filings.csv` - Filing references for 8 BDCs
- ✅ `outputs/arcc_best_soi_table.html` - Sample SOI table from ARCC
- ✅ `Docs/EDGARTOOLS_SPIKE_RESULTS.md` - This document

---

## Decision Point

**Should we switch to EdgarTools approach for Phase 2?**

- ✅ Better data quality (explicit company names)
- ✅ Better coverage (8 vs 4 BDCs immediately)
- ✅ Less engineering risk (no fuzzy matching)
- ✅ Similar or less effort than SEC Data Sets
- ✅ More future-proof

**Recommendation:** YES - Switch to EdgarTools approach
