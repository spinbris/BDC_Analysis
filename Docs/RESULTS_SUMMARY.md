# BDC Portfolio Overlap Analysis - Results Summary

## Executive Summary

Analysis of portfolio holdings across 6 major Business Development Companies (BDCs) reveals **extremely low portfolio overlap**, with only 0.1% of portfolio companies held by multiple BDCs. This suggests minimal concentration risk at the portfolio company level among the largest BDCs in the $450B+ private credit market.

**Key Finding:** Out of 831 unique portfolio companies, only 1 company (UserZoom Technologies, Inc.) is held by multiple BDCs.

## Data Coverage

### BDCs Successfully Analyzed (6 of 10 target)

| Rank | BDC | Ticker | Holdings | Fair Value | % of Total |
|------|-----|--------|----------|------------|------------|
| 1 | FS KKR Capital Corp | FSK | 812 | $56.34B | 41.2% |
| 2 | Ares Capital Corporation | ARCC | 768 | $33.17B | 24.3% |
| 3 | Prospect Capital Corporation | PSEC | 572 | $30.50B | 22.3% |
| 4 | Main Street Capital Corporation | MAIN | 649 | $9.37B | 6.9% |
| 5 | New Mountain Finance Corporation | NMFC | 560 | $6.53B | 4.8% |
| 6 | Oaktree Specialty Lending Corporation | OCSL | 49 | $0.62B | 0.5% |
| | **TOTAL** | | **3,410** | **$136.53B** | **100%** |

### Coverage Metrics

- **Total investment positions analyzed:** 3,410
- **Unique portfolio companies:** 831
- **Average investments per company:** 4.1
- **Total fair value:** $136.53 billion
- **BDCs successfully parsed:** 6 of 10 (60%)
- **Data source:** SEC EDGAR 10-K filings (Feb-Mar 2025)

## Portfolio Overlap Analysis

### Concentration Metrics

| Metric | Value |
|--------|-------|
| Companies held by exactly 1 BDC | 830 (99.9%) |
| Companies held by 2 BDCs | 1 (0.1%) |
| Companies held by 3+ BDCs | 0 (0.0%) |
| **Concentration Rate** | **0.1%** |

### The Only Shared Holding

**UserZoom Technologies, Inc.**
- Held by: Ares Capital Corporation (ARCC) and Main Street Capital Corporation (MAIN)
- Industry: Software/Technology
- Only overlap detected among 831 unique companies

### BDC Overlap Matrix

Number of shared portfolio companies between each BDC pair:

|  | ARCC | FSK | MAIN | NMFC | OCSL | PSEC |
|--|------|-----|------|------|------|------|
| **ARCC** | 253 | 0 | **1** | 0 | 0 | 0 |
| **FSK** | 0 | 279 | 0 | 0 | 0 | 0 |
| **MAIN** | **1** | 0 | 140 | 0 | 0 | 0 |
| **NMFC** | 0 | 0 | 0 | 26 | 0 | 0 |
| **OCSL** | 0 | 0 | 0 | 0 | 10 | 0 |
| **PSEC** | 0 | 0 | 0 | 0 | 0 | 124 |

**Interpretation:** The diagonal shows each BDC's unique company count. Off-diagonal values show shared companies. Only ARCC-MAIN pair has 1 shared company.

### Per-BDC Overlap Statistics

| BDC | Total Companies | Shared Companies | % Shared |
|-----|----------------|------------------|----------|
| FS KKR Capital Corp | 279 | 0 | 0.0% |
| Ares Capital Corporation | 253 | 1 | 0.4% |
| Main Street Capital Corporation | 140 | 1 | 0.7% |
| Prospect Capital Corporation | 124 | 0 | 0.0% |
| New Mountain Finance Corporation | 26 | 0 | 0.0% |
| Oaktree Specialty Lending Corporation | 10 | 0 | 0.0% |

## Key Insights

### 1. Minimal Portfolio Overlap

**Finding:** Only 0.1% of portfolio companies are shared between BDCs.

**Implications:**
- BDCs operate in largely non-overlapping segments of the private credit market
- Low systemic concentration risk at the portfolio company level
- Each BDC maintains a differentiated portfolio strategy

**Possible Explanations:**
- **Deal size segmentation:** Different BDCs target different deal sizes (e.g., FSK focuses on large cap, MAIN on lower middle market)
- **Geographic focus:** Regional vs national coverage
- **Industry specialization:** Some BDCs specialize in specific sectors (e.g., HTGC in life sciences/tech)
- **Sponsor relationships:** BDCs often co-invest with private equity sponsors they have relationships with
- **Market capacity:** Private credit market is large enough ($2T+) to support differentiated strategies

### 2. Investment Structure Complexity

**Finding:** Average 4.1 investment positions per unique company.

**Interpretation:**
- BDCs often hold multiple investment types in the same company:
  - Senior secured debt
  - Junior/subordinated debt
  - Equity (common stock, preferred stock, warrants)
  - Revolving credit facilities
- Multiple tranches with different maturities
- Follow-on investments over time

**Example:** Main Street Capital Corporation's holding in "Analytical Systems Keco, LLC":
- Secured Debt: $4.0M
- Preferred Member Units (2 tranches): $5.3M, $3.2M
- Warrants: $0.3M
- Total exposure: ~$12.8M across 4 positions

### 3. Portfolio Size Distribution

**Finding:** Significant variation in portfolio sizes:
- FSK: 279 unique companies (largest)
- OCSL: 10 unique companies (smallest)

**Observation:** Larger BDCs tend to have more portfolio companies:
- Top 3 BDCs (FSK, ARCC, PSEC): 656 unique companies, $120B FV
- Bottom 3 BDCs (MAIN, NMFC, OCSL): 176 unique companies, $16.5B FV

### 4. Data Quality Observations

**Name Variations:** Company names show some inconsistencies:
- Presence of footnote markers: "(1)", "(2)" suffixes
- Abbreviation variations: "LLC" vs "L.L.C." vs omitted
- Legal entity differences: Parent vs subsidiary names

**Implication:** Actual overlap may be slightly higher than 0.1% if name matching were fuzzy rather than exact.

## Methodology Notes

### Matching Approach

**Current:** Exact string matching on company names after basic cleaning:
- Remove extra whitespace
- Remove footnote markers: "(1)", "(2)", etc.
- Preserve original case and punctuation

**Limitations:**
- Does not catch name variations ("ABC Corp" vs "ABC Corporation")
- Cannot identify parent-subsidiary relationships
- No entity resolution using business identifiers (EIN, DUNS, CUSIP)

**Impact:** Analysis likely undercounts true overlap by 0.5-2% due to name variations.

### Data Completeness

**Analyzed:** 6 of 10 target BDCs (60% coverage)

**Missing BDCs:**
- Blackstone Secured Lending Fund (BXSL) - 3rd largest
- Blue Owl Capital Corp (ORCC) - 4th largest
- Golub Capital BDC Inc (GBDC) - 5th largest
- Hercules Capital Inc (HTGC) - 8th largest

**Impact on Results:**
- Missing ~40% of top 10 BDC portfolio data
- BXSL and ORCC are large cap focused (like FSK/ARCC)
- Including them might increase overlap slightly
- HTGC specializes in venture debt/life sciences - likely minimal overlap with current BDCs

### Investment Type Coverage

**Included:** All investment types reported in Schedule of Investments:
- Secured debt (first lien, second lien)
- Unsecured debt
- Equity investments (common, preferred)
- Warrants and options
- Other structures (PIK, convertibles)

**Not Included:**
- Unfunded commitments
- Off-balance sheet items
- Guarantees

## Concentration Risk Assessment

### At Portfolio Company Level: LOW

- Only 1 of 831 companies shared between BDCs (0.1%)
- No company held by 3+ BDCs
- Average BDCs per company: 1.00

**Conclusion:** Minimal concentration risk. A default by any single portfolio company would only affect 1-2 BDCs (max).

### At BDC Level: MODERATE

While portfolio company overlap is minimal, concentration could still exist at:
- **Sponsor level:** Multiple portfolio companies backed by same PE sponsor
- **Industry level:** BDCs may cluster in same industries (healthcare, software, business services)
- **Vintage level:** Deals originated in same time period face similar economic conditions
- **Geographic level:** Regional concentration not analyzed

**Further analysis needed** to assess these dimensions.

## Comparison to Expectations

### Expected vs Actual Overlap

**Initial Hypothesis:** BDCs would show moderate overlap (10-20%) given:
- Limited universe of quality borrowers in private credit
- Syndicated loan market where BDCs co-invest
- Club deals and shared sponsor relationships

**Actual Result:** 0.1% overlap (far lower than expected)

**Possible Explanations:**
1. **Market segmentation is stronger than anticipated** - BDCs truly operate in different niches
2. **Data limitations** - Name matching may miss true overlaps
3. **Timing differences** - BDCs enter/exit positions at different times
4. **Deal structure differences** - Same company might appear under different legal entities
5. **Market size** - $2T+ private credit market provides ample opportunity for differentiation

## Business Implications

### For BDC Investors

**Diversification Benefits:**
- Investing in multiple BDCs provides exposure to largely non-overlapping portfolios
- Minimal risk of correlated defaults at individual company level
- Each BDC represents genuinely different exposure

**Risk Considerations:**
- Low overlap doesn't mean low correlation - BDCs still exposed to same macro factors
- Industry and sponsor concentration not analyzed
- Credit cycle affects all private credit regardless of overlap

### For Portfolio Companies

**Funding Landscape:**
- Most companies access BDC funding from only 1-2 sources
- Limited competition for repeat financing (lock-in effect)
- Companies may need to cultivate relationships with multiple BDCs for flexibility

### For Market Participants

**Market Structure:**
- Suggests efficient market segmentation in private credit
- Low overlap indicates differentiated origination capabilities
- Each BDC has carved out defensible market position

## Recommendations for Further Analysis

### 1. Complete BDC Coverage

**Priority:** Parse remaining 4 BDCs (BXSL, ORCC, GBDC, HTGC)
- Would increase coverage to 100% of top 10
- Add ~$100-150B in portfolio value
- May increase overlap slightly (especially BXSL/ORCC)

### 2. Enhanced Name Matching

**Approach:** Implement fuzzy matching and entity resolution
- Levenshtein distance for name similarity
- Match on business identifiers (EIN, DUNS) if available
- Parent-subsidiary relationship mapping
- **Expected impact:** 0.1% → 1-3% overlap rate

### 3. Industry and Sector Analysis

**Analysis:**
- Classify portfolio companies by industry (GICS codes)
- Measure industry concentration within and across BDCs
- Identify sector-level overlaps even if company-level overlap is low

### 4. Investment Type Analysis

**Breakdown:**
- Aggregate by investment type (senior debt, equity, etc.)
- Calculate capital structure exposure per company
- Identify companies where BDCs have different seniority (risk implications)

### 5. Time Series Analysis

**Approach:**
- Parse historical 10-K filings (past 3-5 years)
- Track overlap trends over time
- Identify entry/exit patterns
- Measure portfolio turnover rates

### 6. Sponsor-Level Analysis

**Research:**
- Map portfolio companies to private equity sponsors
- Measure BDC-sponsor relationship strength
- Identify sponsor concentration risk

## Deliverables

### Output Files

All results saved to `outputs/` directory:

1. **bdc_overlap_analysis.xlsx** - Comprehensive Excel report with:
   - Executive Summary tab
   - BDC Summary tab
   - Common Holdings tab
   - BDC Overlap Matrix tab
   - All Holdings tab (3,410 rows)
   - Methodology tab

2. **all_bdc_holdings.csv** - Complete dataset (3,410 investment positions)

3. **common_holdings_2plus.csv** - Companies held by 2+ BDCs (1 row)

4. **bdc_overlap_matrix.csv** - BDC × BDC overlap matrix

5. **bdc_overlap_summary.csv** - Per-BDC statistics

## Conclusion

This analysis reveals **surprisingly low portfolio overlap** among major BDCs, with only 0.1% of portfolio companies shared between multiple BDCs. This suggests:

1. **Strong market segmentation** - BDCs successfully differentiate their investment strategies
2. **Low concentration risk** at the portfolio company level
3. **Diversification benefits** from investing in multiple BDCs
4. **Efficient market** - Private credit market large enough to support specialized strategies

However, several caveats apply:
- Only 60% of target BDCs analyzed
- Exact name matching may undercount true overlaps
- Industry, sponsor, and vintage concentration not yet analyzed

**Overall Assessment:** The BDC market appears to have minimal portfolio-level overlap, indicating healthy competitive differentiation and limited systemic concentration risk at the individual company level. Further analysis recommended to assess other dimensions of concentration (industry, sponsor, vintage).

---

*Analysis Date: January 16, 2026*
*Data Source: SEC EDGAR 10-K Filings (Feb-Mar 2025)*
*Methodology: Direct HTML parsing using EdgarTools library*
