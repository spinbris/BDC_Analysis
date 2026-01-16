# BDC Portfolio Industry Analysis - Summary

## Executive Summary

Industry-level analysis of 2 major BDCs (Ares Capital and Main Street Capital) reveals **significant concentration differences** and **minimal cross-BDC competition even within the same sectors**. While company-level overlap is only 0.1%, examining industry concentration provides deeper insights into portfolio composition and risk profiles.

**Key Finding:** ARCC is highly concentrated in Software/Technology (36.2%) and Healthcare (29.9%) with HHI of 2576, while MAIN is more diversified (HHI 1702) across industrial sectors. Even within shared industries like Software/Technology, the two BDCs target different companies (0.7% overlap rate).

## Data Coverage and Limitations

### Coverage
- **BDCs Analyzed:** 2 of 6 successfully parsed BDCs
  - Ares Capital Corporation (ARCC): 253 companies, $33.17B
  - Main Street Capital Corporation (MAIN): 140 companies, $9.37B
- **Total Holdings Analyzed:** 1,417 investment positions
- **Business Description Coverage:** 100% for both BDCs

### Limitations
- **Limited BDC Sample:** Only 2 of 6 BDCs have business descriptions (41.6% coverage)
  - FSK, PSEC, NMFC, OCSL do not have business_description field in parsed data
  - Results may not generalize to other BDCs
- **Classification Method:** Keyword-based classifier may misclassify some companies
- **Sector Granularity:** 16 broad sectors may mask sub-sector differences

## Industry Classification

### Methodology
- **Approach:** Rule-based keyword matching on business descriptions
- **Sectors Identified:** 16 industry categories plus "Other" and "Unknown"
- **Algorithm:** Multi-keyword matching with hierarchical priority

### Industry Sectors
1. Software/Technology
2. Healthcare Services
3. Financial Services
4. Business Services
5. Industrial/Manufacturing
6. Consumer Products
7. Food & Beverage
8. Retail
9. Media & Entertainment
10. Education
11. Energy & Utilities
12. Transportation & Logistics
13. Telecommunications
14. Real Estate
15. Hospitality
16. Agriculture
17. Other (miscellaneous)

## Industry Concentration by BDC

### Ares Capital Corporation (ARCC)

**Portfolio Composition:**
| Industry | Companies | Fair Value | % of Portfolio |
|----------|-----------|------------|----------------|
| Software/Technology | 122 | $12.02B | 36.2% |
| Healthcare Services | 26 | $9.93B | 29.9% |
| Financial Services | 24 | $5.52B | 16.6% |
| Other | 45 | $2.65B | 8.0% |
| Business Services | 12 | $1.62B | 4.9% |
| **Top 3 Total** | **172** | **$27.47B** | **82.8%** |

**Concentration Metrics:**
- **Herfindahl-Hirschman Index (HHI):** 2576
- **Interpretation:** High concentration (HHI > 2500)
- **Industry Diversification:** 14 sectors (excluding Unknown)
- **Largest Single Industry:** Software/Technology (36.2%)

**Sector Focus:**
- Large-cap technology companies (SaaS, cloud platforms, enterprise software)
- Healthcare services and medical technology
- Financial services (insurance, payments, fintech)
- Minimal exposure to traditional industrial/manufacturing

**Risk Profile:**
- High concentration in growth sectors (tech, healthcare)
- Vulnerable to tech sector downturns
- Benefits from high-growth industries
- Less cyclical than industrial-focused portfolios

### Main Street Capital Corporation (MAIN)

**Portfolio Composition:**
| Industry | Companies | Fair Value | % of Portfolio |
|----------|-----------|------------|----------------|
| Other | 44 | $3.04B | 32.4% |
| Industrial/Manufacturing | 27 | $1.76B | 18.8% |
| Software/Technology | 18 | $1.01B | 10.7% |
| Healthcare Services | 6 | $0.65B | 7.0% |
| Business Services | 5 | $0.55B | 5.9% |
| **Top 3 Total** | **89** | **$5.81B** | **62.0%** |

**Concentration Metrics:**
- **Herfindahl-Hirschman Index (HHI):** 1702
- **Interpretation:** Moderate concentration (1500-2500)
- **Industry Diversification:** 16 sectors (excluding Unknown)
- **Largest Single Industry:** Other/Mixed (32.4%)

**Sector Focus:**
- Diversified across many industries (hence large "Other" category)
- Strong industrial/manufacturing presence
- Lower middle market focus (smaller deal sizes)
- More exposure to traditional/cyclical sectors

**Risk Profile:**
- More diversified industry exposure
- Higher cyclical exposure (industrial, manufacturing)
- Less vulnerable to single sector downturns
- Potentially lower growth but more stable

## Cross-BDC Industry Comparison

### Industry Presence Matrix

| Industry | ARCC Companies | MAIN Companies | Total Unique | Overlap |
|----------|---------------|----------------|--------------|---------|
| Software/Technology | 122 | 18 | 139 | 1 (0.7%) |
| Healthcare Services | 26 | 6 | 32 | 0 (0.0%) |
| Financial Services | 24 | 7 | 31 | 0 (0.0%) |
| Industrial/Manufacturing | 9 | 27 | 36 | 0 (0.0%) |
| Business Services | 12 | 5 | 17 | 0 (0.0%) |
| Other | 45 | 44 | 89 | 0 (0.0%) |

### Key Observations

1. **Different Industry Focus:**
   - ARCC dominates Software/Technology (122 vs 18 companies)
   - MAIN dominates Industrial/Manufacturing (27 vs 9 companies)
   - Complementary rather than competitive portfolios

2. **Minimal Within-Industry Overlap:**
   - Even in shared sectors like Software/Technology, only 0.7% overlap
   - UserZoom Technologies is the only shared software company
   - Different sub-sectors or deal sizes within industries

3. **Portfolio Differentiation:**
   - ARCC: Growth-oriented (tech, healthcare)
   - MAIN: Value-oriented (industrial, diversified)
   - Different risk/return profiles

## Industry Overlap Analysis

### The Only Shared Company

**UserZoom Technologies, Inc.**
- **Industry:** Software/Technology
- **BDCs Holding:** ARCC and MAIN
- **Business:** User experience research and testing platform
- **Significance:** Out of 140 software/tech companies held by both BDCs combined, only this 1 overlaps

### Overlap Statistics by Industry

| Industry | ARCC Cos | MAIN Cos | Overlap | Overlap Rate |
|----------|----------|----------|---------|--------------|
| Software/Technology | 122 | 18 | 1 | 0.7% |
| **All Other Industries** | **131** | **122** | **0** | **0.0%** |

**Interpretation:** Even within the most commonly held industry (Software/Technology), overlap is less than 1%. This suggests:
- Different deal size segments (large-cap vs lower middle market)
- Different technology sub-sectors (enterprise vs SMB)
- Geographic differences (national vs regional)
- Different sponsor relationships

## Concentration Risk Assessment

### HHI Interpretation

**Herfindahl-Hirschman Index Scale:**
- **< 1500:** Low concentration (diversified portfolio)
- **1500-2500:** Moderate concentration
- **> 2500:** High concentration

### Individual BDC Risk

**ARCC (HHI 2576 - High Concentration):**
- **Risk:** Vulnerable to tech sector downturns
- **Benefit:** Exposure to high-growth sectors
- **Recommendation:** Monitor tech sector trends closely
- **Diversification:** Could benefit from more industrial exposure

**MAIN (HHI 1702 - Moderate Concentration):**
- **Risk:** Exposure to cyclical industries
- **Benefit:** Better sector diversification
- **Recommendation:** Stable portfolio with balanced exposure
- **Diversification:** Reasonable mix of growth and value sectors

### Systemic Risk

**At Industry Level:** MODERATE
- Two BDCs have very different industry profiles
- ARCC concentrated in growth (tech, healthcare)
- MAIN diversified across traditional sectors
- Limited contagion risk between portfolios

**Comparison to Company Level:** HIGHER
- Company-level concentration: 0.1% (1 of 831 companies)
- Industry-level concentration: 35-36% in top sector for ARCC
- Industry risk affects multiple companies simultaneously
- Tech downturn would impact 36% of ARCC portfolio vs 11% of MAIN

## Strategic Insights

### BDC Investment Strategies

**Ares Capital (ARCC) - Growth Strategy:**
- Focus on high-growth technology and healthcare sectors
- Large-cap private equity backed companies
- Targets scalable businesses with strong unit economics
- Premium valuation multiples, lower yields
- Examples: Enterprise SaaS, cloud platforms, medical devices

**Main Street Capital (MAIN) - Diversified Value Strategy:**
- Diversified across many industries
- Lower middle market focus (smaller businesses)
- Traditional industries (manufacturing, services, retail)
- Higher yields, potential for equity upside
- Examples: Regional manufacturing, local services, franchises

### Market Segmentation

**Deal Size:**
- ARCC: Larger deals ($50M-$500M+)
- MAIN: Smaller deals ($10M-$100M)

**Geographic Focus:**
- ARCC: National/international
- MAIN: Regional/national

**Industry Preference:**
- ARCC: Tech, healthcare (growth sectors)
- MAIN: Industrial, services (traditional sectors)

## Implications for Investors

### Portfolio Diversification Benefits

**Investing in Both BDCs Provides:**
1. **Industry Diversification:**
   - ARCC: Tech/healthcare exposure
   - MAIN: Industrial/services exposure
   - Combined: Balanced sector allocation

2. **Risk Profile Diversification:**
   - ARCC: Growth/higher risk
   - MAIN: Value/moderate risk
   - Combined: Blended risk/return

3. **Cycle Diversification:**
   - ARCC: Benefits from innovation cycles
   - MAIN: Benefits from economic expansion
   - Combined: More stable through cycles

### Risk Considerations

**ARCC Risks:**
- High tech concentration (36%)
- Vulnerable to tech bubble/correction
- Interest rate sensitivity (tech valuations)
- Sector rotation away from growth

**MAIN Risks:**
- Cyclical industry exposure
- Regional economic sensitivity
- Lower growth potential
- Small business default risk

**Combined Risks:**
- Both exposed to credit cycle
- Both sensitive to interest rates
- Macro factors affect both (recession, inflation)
- Regulatory changes (BDC regulation)

## Recommendations for Future Analysis

### 1. Expand BDC Coverage

**Priority:** Parse remaining 4 BDCs to get complete picture
- FSK (FS KKR): Likely similar to ARCC (large-cap focus)
- PSEC (Prospect): Mature portfolio, different vintage
- NMFC (New Mountain): Middle market focus
- OCSL (Oaktree): Distressed/special situations

**Impact:** Would provide more robust industry concentration metrics

### 2. Sub-Sector Analysis

**Drill down within industries:**
- Software: Enterprise SaaS vs vertical SaaS vs infrastructure
- Healthcare: Services vs devices vs pharmaceuticals
- Industrial: Aerospace vs automotive vs general manufacturing

**Method:** Enhanced keyword matching or manual classification

### 3. Geographic Analysis

**Parse location data:**
- Regional concentration
- Urban vs rural
- International exposure

**Source:** Company addresses from filings

### 4. Sponsor Analysis

**Map to private equity sponsors:**
- Identify sponsor relationships
- Measure sponsor concentration
- Track sponsor-BDC co-investment patterns

**Source:** "Affiliates" disclosures in 10-K

### 5. Time Series Analysis

**Track industry allocation over time:**
- Parse historical 10-Ks (3-5 years)
- Measure industry drift
- Identify strategic shifts

**Insight:** Is ARCC moving more into tech or diversifying?

### 6. Enhanced Classification

**Improve classifier:**
- Machine learning-based classification
- Use full business description text
- Cross-reference with industry databases
- Manual review of "Other" category

**Impact:** More accurate sector assignments

## Data Files Generated

All analysis results saved to `outputs/` directory:

1. **all_bdc_holdings_with_industry.csv** - Complete holdings with industry classifications (3,410 rows)

2. **industry_company_counts_by_bdc.csv** - Number of companies by industry and BDC

3. **industry_fair_value_by_bdc.csv** - Fair value ($B) by industry and BDC

4. **industry_overlap_analysis.csv** - Detailed overlap analysis by industry

5. **bdc_industry_analysis.xlsx** - Comprehensive Excel report with 8 tabs:
   - Executive Summary
   - Industry Counts by BDC
   - Industry Fair Value by BDC
   - Industry Overlap
   - ARCC Portfolio (253 companies)
   - MAIN Portfolio (140 companies)
   - Concentration Metrics (HHI)
   - Methodology & Limitations

## Conclusion

Industry-level analysis reveals that while company-level overlap is minimal (0.1%), **industry concentration varies significantly between BDCs**:

- **ARCC** operates a **highly concentrated portfolio** (HHI 2576) focused on growth sectors, with 83% of assets in top 3 industries
- **MAIN** operates a **moderately diversified portfolio** (HHI 1702) across traditional sectors, with 62% in top 3 industries
- Even within shared industries like Software/Technology, **overlap remains minimal** (0.7%), suggesting different market segments

**Key Takeaway:** BDCs differentiate not only by targeting different companies but also by focusing on different industries and segments within industries. This creates complementary rather than competitive portfolios, reducing systemic concentration risk while allowing for investor diversification across sector exposures.

**Limitation:** Analysis covers only 2 of 6 BDCs (41.6% of holdings) due to data availability. Results may differ with full BDC coverage, particularly if FSK (large-cap focus) shows similar tech concentration to ARCC.

---

*Analysis Date: January 16, 2026*
*Data Source: SEC EDGAR 10-K Filings (Feb-Mar 2025)*
*Methodology: Keyword-based industry classification on business descriptions*
*Coverage: 2 BDCs, 1,417 holdings, $42.5B fair value*
