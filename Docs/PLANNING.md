# BDC Portfolio Overlap Analysis - Planning Document

**Created:** January 15, 2026  
**Status:** Phase 1 - Prototype  
**Goal:** Map overlapping portfolio company exposures across top BDCs

---

## Research Question

**How concentrated is private credit exposure across BDCs?**

If multiple large BDCs hold the same portfolio companies, stress in those borrowers could cascade across the BDC sector simultaneously - affecting retail investors, bank credit facilities, and institutional holders.

---

## Data Source: SEC BDC Data Sets

**URL:** https://www.sec.gov/data-research/sec-markets-data/bdc-data-sets

The SEC provides pre-extracted XBRL data from BDC filings, updated monthly.

### Key Tables

| File | Purpose | Key Fields |
|------|---------|------------|
| `soi.tsv` | Schedule of Investments | adsh, cik, portfolio company name, fair value, cost, investment type, industry |
| `sub.tsv` | Submission metadata | adsh, cik, company name, filing date, form type (10-K, 10-Q) |
| `tag.tsv` | Tag definitions | Tag descriptions, taxonomy info |

### Why BDC Data Sets (vs. parsing raw 10-Ks)

- Pre-normalized XBRL extraction by SEC
- Consistent column structure across BDCs
- Monthly updates
- No API rate limiting - single ZIP download
- SOI table is exactly what we need (pivoted holdings data)

### Data Structure Notes

From SEC readme:
- SOI has metadata columns (adsh, cik, form) plus dynamic axis/member columns
- Column positions may change between updates - use column names, not positions
- Custom tags excluded; custom members included

---

## Entity Matching Strategy

**Critical Design Decision: Identifiers First, Fuzzy Last**

Many portfolio companies may have standard identifiers in the XBRL data. We should exhaust identifier-based matching before resorting to fuzzy name matching.

### Matching Priority Order

| Priority | Method | Accuracy | Coverage |
|----------|--------|----------|----------|
| 1 | **CUSIP** | 100% | Unknown - check data |
| 2 | **LEI** (Legal Entity Identifier) | 100% | Unknown - check data |
| 3 | **Portfolio Company CIK** | 100% | Low (most are private) |
| 4 | **Exact name match** | 100% | Moderate |
| 5 | **Normalized name match** | ~99% | Good |
| 6 | **Fuzzy match** (last resort) | ~90% | Fills gaps |

### Why This Order Matters

- **Identifiers are unambiguous** - CUSIP "12345X10" is the same security everywhere
- **Names are messy** - "ABC Holdings, LLC" vs "ABC Holdings LLC" requires logic
- **Fuzzy matching has false positives** - "ABC Corp" might match "ABD Corp" incorrectly
- **Audit trail is cleaner** - Can report "matched by CUSIP" vs "matched by 87% name similarity"

### Phase 1 Will Determine Available Identifiers

Before building matching logic, we need to profile the actual SOI data:

```python
# Discover what identifier columns exist
identifier_patterns = ['cusip', 'lei', 'cik', 'ticker', 'isin', 'identifier', 'id', 'figi']
id_columns = [c for c in soi_df.columns if any(p in c.lower() for p in identifier_patterns)]

# Check population rates
for col in id_columns:
    populated = soi_df[col].notna().sum()
    total = len(soi_df)
    print(f"{col}: {populated}/{total} ({populated/total:.1%})")
```

---

## Phased Implementation

### Phase 1: Prototype + Data Profiling

**Goal:** Download data, understand structure, prove concept with exact matching

**Tasks:**

1. **Download & Extract**
   - Download current BDC Data Set ZIP from SEC
   - Extract to `data/raw/`

2. **Data Profiling (CRITICAL)**
   - Load `soi.tsv` and inspect ALL column names
   - Identify potential identifier columns (CUSIP, LEI, CIK, etc.)
   - Check population rates for each identifier
   - Sample data to understand structure
   - Document findings in `Docs/DATA_PROFILE.md`

3. **Basic Loading**
   - Load `sub.tsv` for BDC metadata
   - Filter SOI to top 10 BDCs by CIK
   - Identify column containing portfolio company names

4. **Simple Overlap (Exact Match)**
   - Find companies appearing in 2+ BDCs using exact name match
   - Output basic overlap matrix

5. **Excel Output**
   - BDC summary tab
   - Overlapping companies tab
   - BDC × BDC overlap matrix

**Modules to Create:**
```
src/
├── __init__.py
├── download.py      # download_bdc_dataset()
├── load.py          # load_soi(), load_submissions(), filter_top_bdcs()
├── profile.py       # profile_soi_columns(), check_identifiers()  <-- NEW
├── overlap.py       # find_common_holdings(), build_overlap_matrix()
└── export.py        # to_excel()
```

**Success Criteria:**
- [ ] Data downloaded and loaded successfully
- [ ] **Identifier columns documented** (what exists, population rates)
- [ ] Can identify companies held by 2+ BDCs (exact match)
- [ ] Excel output validates against spot-check of raw filing
- [ ] Clear recommendation on matching strategy for Phase 2

**Estimated Time:** 2-3 days

---

### Phase 2: Entity Resolution

**Goal:** Implement tiered matching strategy based on Phase 1 findings

**Approach depends on Phase 1 data profiling:**

#### Scenario A: Good Identifier Coverage (>50% have CUSIP/LEI)
- Match by identifier first
- Exact name match for remainder
- Minimal fuzzy matching needed

#### Scenario B: Poor Identifier Coverage (<20%)
- Exact name match first
- Normalized name match second
- Fuzzy match as fallback with manual review

**Tasks:**

1. **Identifier Matching** (if available)
   - Join on CUSIP/LEI/CIK where populated
   - Track match source for audit

2. **Name Normalization**
   ```python
   def normalize_company_name(name: str) -> str:
       name = name.lower().strip()
       # Remove punctuation
       name = re.sub(r'[^\w\s]', '', name)
       # Standardize legal suffixes
       suffixes = ['llc', 'inc', 'corp', 'corporation', 'ltd', 'limited', 'lp', 'lllp']
       for suffix in suffixes:
           name = re.sub(rf'\b{suffix}\b', '', name)
       # Remove extra whitespace
       return ' '.join(name.split())
   ```

3. **Fuzzy Matching** (last resort)
   - Use rapidfuzz token_set_ratio
   - Threshold 90+ for auto-match
   - 80-90 flagged for manual review
   - Industry matching as secondary signal

4. **Entity Master Table**
   - Create canonical entity list
   - Map all variants to canonical ID
   - Store match method and confidence

**Modules to Create/Update:**
```
src/
├── normalize.py     # normalize_name(), match_by_identifier(), fuzzy_match()
data/
├── processed/
│   └── entity_master.csv   # Canonical entity mappings
│   └── manual_overrides.csv # Human-verified matches
```

**Success Criteria:**
- [ ] >95% of holdings matched to canonical entity
- [ ] Match method tracked for each (identifier/exact/normalized/fuzzy)
- [ ] Manual review completed for uncertain matches
- [ ] Validation against sample of raw filings

**Estimated Time:** 3-4 days

---

### Phase 3: Rich Analysis

**Goal:** Comprehensive overlap metrics with dollar exposures

**Tasks:**

1. **Aggregate Holdings**
   - Sum fair value by (BDC, canonical_entity)
   - Track investment types per holding

2. **Overlap Matrices**
   - Company × BDC matrix (values = fair value)
   - BDC × BDC matrix (values = shared company count)
   - BDC × BDC matrix (values = shared $ exposure)

3. **Concentration Metrics**
   - Top 20 most commonly held companies
   - Total $ at risk per company (sum across all BDC holders)
   - HHI-style concentration index
   - "If Company X defaults, which BDCs lose how much?"

4. **Investment Type Analysis**
   - 1st lien overlap vs subordinated overlap
   - Equity co-investments

**Modules to Update:**
```
src/
├── overlap.py       # Add value-weighted functions, concentration metrics
├── export.py        # Multi-tab Excel with charts
```

**Success Criteria:**
- [ ] Top 20 overlapping companies with total exposure quantified
- [ ] Can answer: "Company X default impacts BDCs A, B, C for $X, $Y, $Z"
- [ ] Investment type breakdown available

**Estimated Time:** 2-3 days

---

### Phase 4: Historical Analysis

**Goal:** Track overlap changes over time

**Tasks:**

1. **Historical Data Collection**
   - Download quarterly BDC Data Sets (~2 years back)
   - Store in `data/raw/YYYY-QN/`

2. **Time Series Analysis**
   - Run overlap analysis for each period
   - Track metrics over time:
     - Number of overlapping companies
     - Average overlap count
     - Concentration trend

3. **Change Detection**
   - New overlaps (companies newly held by 2+ BDCs)
   - Exits (companies no longer commonly held)
   - Concentration increasing or decreasing?

**Modules to Update:**
```
src/
├── download.py      # Support historical downloads
├── overlap.py       # Time series comparison functions
```

**Success Criteria:**
- [ ] 8+ quarters of historical data
- [ ] Trend visualization
- [ ] Notable changes identified

**Estimated Time:** 2-3 days

---

### Phase 5: Integration & Reporting

**Goal:** Final outputs for NBFI systemic risk research

**Deliverables:**

1. **Excel Workbook** (`outputs/bdc_overlap_analysis.xlsx`)
   - Summary statistics
   - Top overlapping companies
   - BDC × BDC matrix
   - Historical trends
   - Methodology notes

2. **Visualizations**
   - Overlap heatmap
   - Concentration trend chart
   - Optional: Network graph

3. **Research Integration**
   - Summary text for NBFI research document
   - Key statistics and findings
   - Methodology and limitations

**Estimated Time:** 1-2 days

---

## Module Architecture

```
src/
├── __init__.py
│
├── download.py
│   └── download_bdc_dataset(output_dir: Path, period: str = "latest") -> Path
│       # Downloads ZIP from SEC, extracts to output_dir
│       # period="latest" or "2024q3" for historical
│
├── load.py
│   ├── load_submissions(path: Path) -> pd.DataFrame
│   │   # Load sub.tsv, return BDC metadata
│   │
│   ├── load_soi(path: Path) -> pd.DataFrame
│   │   # Load soi.tsv, return holdings data
│   │
│   └── filter_top_bdcs(soi_df, sub_df, ciks: list = None) -> pd.DataFrame
│       # Filter to specified CIKs or top N by assets
│
├── profile.py  # NEW - Phase 1 data exploration
│   ├── profile_columns(df: pd.DataFrame) -> dict
│   │   # Categorize columns: metadata, identifiers, values
│   │
│   ├── check_identifier_coverage(df: pd.DataFrame) -> pd.DataFrame
│   │   # Report population rates for potential identifiers
│   │
│   └── generate_data_profile_report(soi_df, output_path: Path) -> None
│       # Create DATA_PROFILE.md with findings
│
├── normalize.py  # Phase 2
│   ├── normalize_company_name(name: str) -> str
│   │   # Clean and standardize company name
│   │
│   ├── match_by_identifier(df: pd.DataFrame, id_col: str) -> pd.DataFrame
│   │   # Match records with same identifier
│   │
│   ├── match_by_name(df: pd.DataFrame, threshold: int = 90) -> pd.DataFrame
│   │   # Exact, normalized, then fuzzy matching
│   │
│   └── build_entity_master(soi_df, overrides_path: Path = None) -> pd.DataFrame
│       # Create canonical entity mapping table
│
├── overlap.py
│   ├── build_holdings_matrix(soi_df, value_col: str = None) -> pd.DataFrame
│   │   # Rows=companies, Cols=BDCs, Values=fair_value or 1/0
│   │
│   ├── calculate_bdc_overlap(matrix: pd.DataFrame) -> pd.DataFrame
│   │   # BDC × BDC matrix of shared holdings count
│   │
│   ├── find_common_holdings(matrix: pd.DataFrame, min_holders: int = 2) -> pd.DataFrame
│   │   # Companies held by N+ BDCs with holder list
│   │
│   └── concentration_metrics(matrix: pd.DataFrame) -> dict  # Phase 3
│       # HHI, top N concentration, exposure at risk
│
└── export.py
    ├── to_excel(results: dict, output_path: Path) -> None
    │   # Write multi-tab Excel workbook
    │
    └── overlap_heatmap(matrix: pd.DataFrame, output_path: Path) -> None  # Phase 5
        # Generate heatmap visualization
```

---

## CIK Reference (Top 10 BDCs)

```python
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
```

*Note: Verify CIKs against `sub.tsv` on first data load.*

---

## SEC Download Details

**URL:**
```
https://www.sec.gov/files/dera/data/bdc-data-sets/bdc-data-sets.zip
```

**Required Headers:**
```python
HEADERS = {
    'User-Agent': 'BDC Analysis Project contact@example.com',
    'Accept-Encoding': 'gzip, deflate',
}
```

**ZIP Contents:**
```
bdc-data-sets/
├── readme.htm
├── sub.tsv      # Submission metadata
├── tag.tsv      # Tag definitions
├── num.tsv      # Numeric values
├── txt.tsv      # Text values
├── pre.tsv      # Presentation
├── cal.tsv      # Calculations
├── non.tsv      # Non-financial filings
└── soi.tsv      # Schedule of Investments <-- PRIMARY
```

---

## Timeline Summary

| Phase | Duration | Cumulative | Key Deliverable |
|-------|----------|------------|-----------------|
| Phase 1 | 2-3 days | 2-3 days | Data profile + basic overlap |
| Phase 2 | 3-4 days | 5-7 days | Entity resolution |
| Phase 3 | 2-3 days | 7-10 days | Rich metrics |
| Phase 4 | 2-3 days | 9-13 days | Historical trends |
| Phase 5 | 1-2 days | 10-15 days | Final report |

**Total:** ~2 weeks for full implementation

---

## Next Steps

**To start Phase 1, tell Claude Code:**

> "Read Docs/PLANNING.md and implement Phase 1. Start with the download module, then load and profile the data. I want to see what identifier columns exist before we design the matching strategy."

Claude Code will:
1. Create project structure and dependencies
2. Build download module
3. Build load module  
4. Build profile module
5. Run profiling and report findings
6. Implement basic overlap with exact matching
7. Generate Excel output

**Key Phase 1 output:** `Docs/DATA_PROFILE.md` documenting available identifiers
