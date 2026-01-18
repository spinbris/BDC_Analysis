---
name: bdc-xbrl-extraction
description: Extract Schedule of Investments data from BDC 10-K/10-Q filings using XBRL taxonomy. Covers BOTH debt investments (senior secured loans, subordinated debt, etc.) AND equity investments (common stock, preferred, warrants, LLC units). Extracts from SEC Reg S-X Schedules 12-12 (unaffiliated) and 12-13 (affiliated). Use when extracting portfolio holdings, investment positions, fair values, loan data, or company-level data from Business Development Company SEC filings. Triggers on: BDC portfolio extraction, Schedule of Investments parsing, investment company holdings analysis, private credit portfolio data, loan book analysis.
---

# BDC Schedule of Investments Extraction

Extract structured portfolio data from Business Development Company SEC filings.

## Overview

BDCs file a **Consolidated Schedule of Investments** in 10-K/10-Q containing:
- **Debt Investments**: Senior secured loans, subordinated debt, mezzanine, unitranche
- **Equity Investments**: Common stock, preferred stock, warrants, LLC/LP units

Data comes from SEC Reg S-X Article 12:
- **Schedule 12-12**: Investments in Securities of Unaffiliated Issuers
- **Schedule 12-13**: Investments in and Advances to Affiliates

All use **Inline XBRL** (required since Aug 2022) with the **US GAAP Investment Company Taxonomy**.

## Validated Results

Tested and validated on 4 major BDCs (Jan 2025):

| BDC | Ticker | Debt | Equity | Total FV | Status |
|-----|--------|------|--------|----------|--------|
| Ares Capital | ARCC | 1,239 | 427 | $35.6B | ✅ |
| Main Street Capital | MAIN | 452 | 204 | $5.4B | ✅ |
| FS KKR Capital | FSK | 541 | 153 | $19.9B | ✅ |
| Hercules Capital | HTGC | 261 | 258 | $7.3B | ✅ |
| **Total** | | **2,493** | **1,042** | **$68.2B** | |

## Critical Implementation Notes

### 1. Data is Split Across Multiple Statements

SOI data is NOT in one clean table. It's distributed across:
- **Schedule of Investments** → Interest rates, spreads, maturity dates
- **Balance Sheet** → Fair values
- **Balance Sheet Parenthetical** → Cost basis

**Must query all statements and join by investment ID.**

### 2. Investment IDs are in Context Dimensions

Investment identifiers are NOT in fact values. They're in XBRL context dimensions:

```python
# WRONG - won't find IDs
facts_df['investment_id']  # Doesn't exist as column

# CORRECT - access via contexts
context_ref = fact['context_ref']
dimensions = xbrl.contexts[context_ref].dimensions
investment_id = dimensions.get('InvestmentIdentifierAxis')
```

### 3. Namespace Prefixes Vary - Always Normalize

Different BDCs use different namespace prefixes:
- `us-gaap:InvestmentOwnedAtFairValue`
- `InvestmentOwnedAtFairValue` (no prefix)
- `arcc:CustomElement`

**Always strip namespace when matching:**

```python
def normalize_concept(concept: str) -> str:
    """Strip namespace prefix for consistent matching."""
    if not concept:
        return concept
    if ':' in concept:
        return concept.split(':', 1)[1]
    return concept
```

### 4. Classification Rate is 67-81%

Not all positions classify cleanly. Expect:
- 67-81% classified as Debt or Equity
- 19-33% unclassified (aggregate rollups, sector totals, etc.)

Unclassified positions are typically aggregate dimension members, not individual investments.

## Output Structure

```
{TICKER}_10K_debt_investments.csv      # Loans with rate/maturity data
{TICKER}_10K_equity_investments.csv    # Equity with shares/ownership data  
{TICKER}_10K_affiliated_rollforward.csv # Affiliated investment activity
{TICKER}_10K_portfolio_summary.csv     # Totals by type, industry, affiliation
```

## Quick Start

### CLI Usage

```bash
python extract_soi.py ARCC --identity "Your Name your@email.com"
python extract_soi.py MAIN 10-Q --identity "Your Name your@email.com"
python extract_soi.py FSK 10-K 2023 --identity "Your Name your@email.com"
```

### Python Usage

```python
from edgar import Company, set_identity

set_identity("Your Name your@email.com")

company = Company("ARCC")
filing = company.get_filings(form="10-K").latest()
xbrl = filing.xbrl()

# Use the extraction functions from extract_soi.py
from extract_soi import extract_all_investments
debt_df, equity_df, affiliated_df, summary_df = extract_all_investments(xbrl)
```

## Key XBRL Elements

### Core Elements (Both Debt and Equity)

| Field | Element (no namespace) | Description |
|-------|------------------------|-------------|
| Fair Value | `InvestmentOwnedAtFairValue` | Current fair value |
| Cost | `InvestmentOwnedAtCost` | Amortized cost basis |
| % Net Assets | `InvestmentOwnedPercentOfNetAssets` | Position size |

### Debt-Specific Elements

| Field | Element | Description |
|-------|---------|-------------|
| Principal | `InvestmentOwnedBalancePrincipalAmount` | Outstanding principal |
| Interest Rate | `InvestmentInterestRate` | Stated rate |
| Spread | `InvestmentBasisSpreadVariableRate` | Spread over base |
| Floor | `InvestmentInterestRateFloor` | Rate floor |
| PIK Rate | `InvestmentInterestRatePaidInKind` | PIK component |
| Maturity | `InvestmentMaturityDate` | Due date |

### Equity-Specific Elements

| Field | Element | Description |
|-------|---------|-------------|
| Shares | `InvestmentOwnedBalanceShares` | Shares/units held |

### Extensible Enumerations

| Field | Element | Notes |
|-------|---------|-------|
| Issuer Name | `InvestmentIssuerNameExtensibleEnumeration` | Portfolio company |
| Investment Type | `InvestmentTypeExtensibleEnumeration` | Loan type, stock class |
| Industry | `InvestmentIndustrySectorExtensibleEnumeration` | Sector |
| Affiliation | `InvestmentIssuerAffiliationExtensibleEnumeration` | Affiliated/Unaffiliated |
| Rate Type | `InvestmentVariableInterestRateTypeExtensibleEnumeration` | SOFR, Prime, etc. |

## Investment ID Format Examples

Investment IDs from context dimensions vary by BDC:

```
# ARCC format
"Actfy Buyer, Inc., First lien senior secured loan"
"ABC Company, Class A common stock"

# MAIN format  
"XYZ Holdings LLC - Senior Secured Term Loan"
"Portfolio Co Inc - Common Equity"

# FSK format
"Company Name | First Lien Term Loan | SOFR+500"
```

**Entity resolution will require fuzzy matching or normalization.**

## Debt vs Equity Classification

The script classifies using multiple signals:

1. **Investment Type Keywords**
   - Debt: loan, debt, note, bond, credit, mezzanine, senior, subordinated
   - Equity: stock, equity, share, warrant, unit, membership, preferred, common

2. **Field Presence**
   - Has Principal + no Shares → Debt
   - Has Shares + no Principal → Equity

3. **Investment Type Axis** (for totals)
   - `DebtSecuritiesMember`
   - `EquitySecuritiesMember`

## Common Issues & Solutions

### "No Schedule of Investments facts found"

**Cause**: Querying wrong concepts or not accessing contexts correctly

**Solution**: 
1. Query all facts, filter by normalized concept name
2. Access investment IDs from `xbrl.contexts[context_ref].dimensions`

### "Namespace prefix issues"

**Cause**: Concept has `us-gaap:` prefix in some filings, not others

**Solution**: Always use `normalize_concept()` to strip prefixes

### "Low classification rate"

**Cause**: Aggregate dimension members (sector totals, rollups) aren't individual investments

**Solution**: This is expected. Focus on classified positions for analysis.

### "Investment ID parsing"

**Cause**: ID formats vary widely across BDCs

**Solution**: For entity resolution/overlap analysis, will need:
- Fuzzy matching
- Company name normalization
- Possibly LEI/CIK lookup

## Data Quality Expectations

Based on testing across 4 BDCs:

| Metric | Expected Coverage |
|--------|-------------------|
| Fair Value | 100% |
| Cost Basis | 97-100% |
| Principal (debt) | 70-75% |
| Shares (equity) | 25-30% |
| Interest Rate | 65-70% |
| Classification Rate | 67-81% |

## See Also

- [xbrl-elements.md](references/xbrl-elements.md) - Complete element reference
- [taxonomy-dimensions.md](references/taxonomy-dimensions.md) - Dimensional modeling guide
- [extract_soi.py](scripts/extract_soi.py) - Working extraction script
- FASB Implementation Guide: https://xbrl.fasb.org/impguidance/BDC_TIG/
