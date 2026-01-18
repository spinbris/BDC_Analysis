# BDC Portfolio Database

SQLite database for analyzing BDC portfolio holdings, overlap, and industry concentration.

## Quick Start

```bash
# Initialize database and load existing CSV data
cd /Users/stephenparton/projects/BDC_Analysis
python src/db_loader.py

# Schema only (no data)
python src/db_loader.py --schema-only

# Load specific CSV
python src/db_loader.py --csv outputs/all_bdc_holdings_with_industry.csv
```

## Database Location

```
data/bdc_portfolio.db
```

## Schema Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│      bdc        │     │   portfolio_    │     │    industry     │
│                 │     │   company       │     │                 │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ ticker (PK)     │     │ id (PK)         │     │ code (PK)       │
│ name            │     │ normalized_name │     │ name            │
│ cik             │     │ business_desc   │◄────│ sector          │
│ total_assets    │     │ assigned_indust │     │ parent_sector   │
└────────┬────────┘     │ sic_code        │     └─────────────────┘
         │              │ naics_code      │
         │              │ classification_ │
         │              │   method        │
         │              │ confidence_score│
         │              │ lei             │
         │              └────────┬────────┘
         │                       │
         ▼                       ▼
┌───────────────────────────────────────────┐
│              investment                    │
├───────────────────────────────────────────┤
│ id (PK)                                    │
│ bdc_ticker (FK) ──────────────────────────┤
│ company_id (FK) ──────────────────────────┤
│ investment_type                            │
│ asset_class      (Debt/Equity)            │
│ fair_value                                 │
│ cost                                       │
│ principal        (debt only)              │
│ shares           (equity only)            │
│ interest_rate                              │
│ spread                                     │
│ rate_type                                  │
│ maturity_date                              │
│ period_end       (time series key)        │
│ filing_date                                │
│ fiscal_year                                │
│ fiscal_quarter                             │
└───────────────────────────────────────────┘

┌───────────────────────────────────────────┐
│        company_embedding (Phase 2)        │
├───────────────────────────────────────────┤
│ company_id (FK)                           │
│ embedding (BLOB)                          │
│ model_name                                │
│ model_version                             │
└───────────────────────────────────────────┘
```

## Common Queries

### Portfolio Overlap

```sql
-- Companies held by multiple BDCs
SELECT * FROM v_overlap_companies
ORDER BY bdc_count DESC, total_fair_value DESC;

-- Direct query with more detail
SELECT 
    pc.normalized_name,
    pc.assigned_industry,
    COUNT(DISTINCT i.bdc_ticker) as bdc_count,
    GROUP_CONCAT(DISTINCT i.bdc_ticker) as bdcs,
    SUM(i.fair_value) as total_exposure
FROM portfolio_company pc
JOIN investment i ON pc.id = i.company_id
GROUP BY pc.id
HAVING bdc_count > 1
ORDER BY total_exposure DESC;
```

### Industry Concentration

```sql
-- Industry breakdown by BDC
SELECT * FROM v_industry_concentration
WHERE bdc_ticker = 'ARCC'
ORDER BY total_fair_value DESC;

-- Cross-BDC industry exposure
SELECT 
    pc.assigned_industry,
    COUNT(DISTINCT i.bdc_ticker) as bdc_count,
    COUNT(DISTINCT pc.id) as company_count,
    SUM(i.fair_value) as total_exposure
FROM investment i
JOIN portfolio_company pc ON i.company_id = pc.id
WHERE pc.assigned_industry IS NOT NULL
GROUP BY pc.assigned_industry
ORDER BY total_exposure DESC;
```

### Stress Testing

```sql
-- What if Software sector drops 30%?
SELECT 
    i.bdc_ticker,
    SUM(i.fair_value) as current_exposure,
    SUM(i.fair_value * 0.30) as potential_loss
FROM investment i
JOIN portfolio_company pc ON i.company_id = pc.id
WHERE pc.assigned_industry = 'SOFTWARE'
GROUP BY i.bdc_ticker
ORDER BY potential_loss DESC;
```

### Time Series (when multiple periods loaded)

```sql
-- Position changes over time
SELECT 
    pc.normalized_name,
    i.period_end,
    i.fair_value,
    LAG(i.fair_value) OVER (PARTITION BY i.company_id ORDER BY i.period_end) as prev_fair_value,
    i.fair_value - LAG(i.fair_value) OVER (PARTITION BY i.company_id ORDER BY i.period_end) as change
FROM investment i
JOIN portfolio_company pc ON i.company_id = pc.id
WHERE i.bdc_ticker = 'ARCC'
ORDER BY pc.normalized_name, i.period_end;
```

## Python API

```python
from src.db_loader import BDCDatabase

with BDCDatabase() as db:
    # Get summary
    summary = db.get_bdc_summary()
    
    # Get overlap
    overlap = db.get_overlap_summary()
    
    # Get industry concentration
    industry = db.get_industry_concentration(bdc_ticker='ARCC')
    
    # Direct SQL
    df = pd.read_sql_query("SELECT * FROM investment LIMIT 10", db.conn)
```

## Adding New Data

### Load a new CSV extract

```python
with BDCDatabase() as db:
    db.load_from_csv(
        csv_path=Path("outputs/new_holdings.csv"),
        period_end="2024-12-31"  # Specify the period
    )
```

### Add individual records

```python
with BDCDatabase() as db:
    # Add BDC
    ticker = db.get_or_create_bdc("New BDC Name", cik="1234567")
    
    # Add company
    company_id = db.get_or_create_company(
        name="Portfolio Company Inc.",
        business_desc="Software for widgets",
        industry_sector="Software/Technology"
    )
    
    # Add investment
    db.add_investment(
        bdc_ticker=ticker,
        company_id=company_id,
        investment_type="First lien senior secured loan",
        fair_value=10000000,
        cost=10000000,
        principal=10000000,
        period_end="2024-09-30"
    )
```

## Future Extensions (Phase 2)

### Semantic Search with Embeddings

When ready to add semantic search:

1. Install dependencies: `pip install sentence-transformers numpy`
2. Generate embeddings from `business_desc`
3. Store in `company_embedding` table
4. Query with cosine similarity

```python
# Future implementation sketch
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')

# Generate embeddings
for company in companies:
    embedding = model.encode(company.business_desc)
    # Store in company_embedding table

# Semantic search
query_embedding = model.encode("healthcare technology")
# Find similar companies by cosine similarity
```

## Classification Methods

The `classification_method` field tracks how `assigned_industry` was determined:

| Method | Description |
|--------|-------------|
| `SIC` | From SIC code in filing |
| `NAICS` | From NAICS code in filing |
| `KEYWORD` | Keyword matching on business_desc |
| `LLM` | LLM classification (future) |
| `MANUAL` | Human review |
| `NULL` | Not yet classified |

## Notes

- **Entity Resolution**: Currently uses conservative name normalization. Companies must match exactly after normalization. Fuzzy matching planned for Phase 2.
- **Time Series**: Each `investment` record is tied to a `period_end` date. Load multiple periods to track changes.
- **Unique Constraint**: The `investment` table prevents exact duplicates per period.
