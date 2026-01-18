# BDC XBRL Taxonomy Dimensions

Guide to dimensional modeling in BDC Schedule of Investments XBRL filings.

## Critical: How to Access Investment IDs

Investment identifiers are stored in **XBRL context dimensions**, NOT as fact values.

### Correct Access Pattern

```python
# Get a fact
fact = facts_df.iloc[0]
context_ref = fact['context_ref']

# Access the context
context = xbrl.contexts[context_ref]

# Get investment ID from dimensions
if hasattr(context, 'dimensions'):
    investment_id = context.dimensions.get('InvestmentIdentifierAxis')
```

### Common Mistake

```python
# WRONG - investment_id is not a column in facts DataFrame
investment_id = fact['investment_id']  # KeyError!

# WRONG - dimensions in DataFrame may be empty/different format
investment_id = fact['dimensions']['InvestmentIdentifierAxis']  # Often fails
```

## Investment ID Format Examples

IDs vary significantly across BDCs:

```
# ARCC
"Actfy Buyer, Inc., First lien senior secured loan"
"ABC Holdings LLC, Class A common stock"
"XYZ Corp, Senior secured revolving credit facility"

# MAIN
"Company Name - Senior Secured Term Loan"
"Portfolio Co Inc - Common Equity"
"Holdings LLC - Subordinated Debt"

# FSK
"Company Name | First Lien Term Loan | SOFR+500"
"Issuer Inc | Common Stock"

# HTGC
"Company, Inc. - Term Loan A"
"Tech Startup LLC - Series A Preferred"
```

**For entity resolution, you'll need fuzzy matching or normalization.**

## Dimension Types

### Typed Dimension: InvestmentIdentifierAxis

**Purpose**: Uniquely identify each individual investment position

**Key Characteristics**:
- Members are NOT in the taxonomy
- Members are unique strings created per-filing
- Associates all data points for a single investment together
- **Accessed via xbrl.contexts, not fact dimensions column**

### Explicit Dimensions (for Totals/Aggregations)

These ARE in the taxonomy and used for subtotals:

| Axis | Purpose | Key Members |
|------|---------|-------------|
| `InvestmentIssuerAffiliationAxis` | Affiliated vs Unaffiliated totals | `InvestmentUnaffiliatedIssuerMember`, `InvestmentAffiliatedIssuerMember` |
| `InvestmentTypeAxis` | Debt vs Equity totals | `DebtSecuritiesMember`, `EquitySecuritiesMember` |
| `EquitySecuritiesByIndustryAxis` | Industry breakdown | `TechnologySectorMember`, `HealthcareSectorMember`, etc. |

## Dimension Hierarchy

### InvestmentIssuerAffiliationAxis

```
InvestmentIssuerAffiliationDomain
├── InvestmentUnaffiliatedIssuerMember (<5% ownership)
└── InvestmentAffiliatedIssuerMember (5%+ ownership)
    ├── InvestmentAffiliatedIssuerControlledMember (>25%)
    └── InvestmentAffiliatedIssuerNoncontrolledMember (5-25%)
```

### InvestmentTypeAxis

```
InvestmentTypeCategorizationMember
├── DebtSecuritiesMember
└── EquitySecuritiesMember
```

## Identifying Individual vs Aggregate Facts

### Individual Investment Facts

Have `InvestmentIdentifierAxis` in their context:

```python
def is_individual_investment(xbrl, context_ref):
    context = xbrl.contexts.get(context_ref)
    if context and hasattr(context, 'dimensions'):
        return 'InvestmentIdentifierAxis' in context.dimensions
    return False
```

### Aggregate/Total Facts

Have explicit dimension axes WITHOUT `InvestmentIdentifierAxis`:

```python
# This is a total by affiliation type
{
    'concept': 'InvestmentOwnedAtFairValue',
    'value': 21721000,
    'dimensions': {
        'InvestmentIssuerAffiliationAxis': 'InvestmentUnaffiliatedIssuerMember'
    }
}
```

### Report-Wide Totals

No dimensions at all:

```python
# Grand total - all investments
{
    'concept': 'InvestmentOwnedAtFairValue',
    'value': 35600000000,
    'dimensions': None
}
```

## Extracting Data by Investment

### Pattern: Build Investment Records

```python
from collections import defaultdict

def extract_investments(xbrl, facts_df):
    """Group facts by investment ID from contexts."""
    investments = defaultdict(dict)
    
    for _, fact in facts_df.iterrows():
        context_ref = fact.get('context_ref')
        if not context_ref:
            continue
            
        # Get context and check for investment dimension
        context = xbrl.contexts.get(context_ref)
        if not context or not hasattr(context, 'dimensions'):
            continue
            
        inv_id = context.dimensions.get('InvestmentIdentifierAxis')
        if not inv_id:
            continue  # Skip aggregates
        
        # Map concept to field name
        concept = normalize_concept(fact['concept'])
        value = fact['value']
        
        investments[inv_id][concept] = value
    
    return dict(investments)
```

## Affiliation Categories

| Category | Ownership Level | How to Identify |
|----------|-----------------|-----------------|
| Unaffiliated | <5% | `InvestmentUnaffiliatedIssuerMember` in dimensions OR affiliation enumeration |
| Non-Controlled Affiliate | 5-25% | `InvestmentAffiliatedIssuerNoncontrolledMember` |
| Controlled Affiliate | >25% | `InvestmentAffiliatedIssuerControlledMember` |

## Classification Rate Expectations

Based on testing across 4 BDCs:

| BDC | Classified | Unclassified | Rate |
|-----|------------|--------------|------|
| ARCC | 1,666 | 384 | 81% |
| MAIN | 656 | 196 | 77% |
| FSK | 694 | 208 | 77% |
| HTGC | 519 | 256 | 67% |

**Unclassified positions are typically:**
- Sector/industry totals
- Aggregate rollup dimensions
- Summary line items

These are NOT missing data - they're intentionally aggregate facts.

## Key Takeaways

1. **Investment IDs are in contexts** - Access via `xbrl.contexts[context_ref].dimensions`

2. **Individual vs Aggregate** - Check for `InvestmentIdentifierAxis` presence

3. **ID formats vary** - Each BDC uses different naming conventions

4. **Explicit dimensions for totals** - Affiliation, Type, Industry axes are for aggregates

5. **67-81% classification is normal** - Unclassified items are aggregates, not errors

6. **Entity resolution needed** - For overlap analysis, must normalize/match company names across BDCs
