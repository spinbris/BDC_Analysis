# CLAUDE.md

## Project Overview

**BDC Portfolio Overlap Analysis** - Extracts and analyzes portfolio holdings across Business Development Companies (BDCs) to assess concentration risk in the private credit market.

## Current State

Working pipeline extracts Schedule of Investments data from SEC EDGAR XBRL filings into SQLite database. 10 BDCs loaded across 2022-2024 with 161 overlapping companies identified.

## Repository Structure

```
BDC_Analysis/
├── CLAUDE.md              # This file
├── data/
│   ├── bdc_portfolio.db   # SQLite database with holdings data
│   └── raw/bdc-data-sets/ # SEC BDC Data Sets (reference)
├── src/
│   ├── bdc_pipeline.py    # Main extraction: EDGAR XBRL → SQLite
│   ├── db_loader.py       # Database operations
│   └── classify_industries.py
├── analysis/              # R/Quarto analysis notebooks
├── db/
│   └── schema.sql         # Database schema reference
└── Docs/
    └── PLANNING.md        # Historical planning doc
```

## Key Commands

```bash
# Extract/reload BDC data
python src/bdc_pipeline.py --compliant --years 2022 2023 2024

# Reset database and reload
python src/bdc_pipeline.py --reset --compliant --years 2022 2023 2024

# Check database status
python src/bdc_pipeline.py --status

# List available BDCs
python src/bdc_pipeline.py --list
```

## Database Schema

**Tables:**
- `bdcs` - BDC metadata (ticker, name, CIK)
- `companies` - Portfolio companies (name, industry)
- `holdings` - Investment positions (BDC → company, fair_value, cost, period)

**Key queries:**
```sql
-- Holdings by period
SELECT * FROM holdings WHERE period_end = '2024-12-31';

-- Overlap companies (held by 2+ BDCs)
SELECT company_id, COUNT(DISTINCT bdc_ticker) as bdc_count
FROM holdings
GROUP BY company_id
HAVING bdc_count >= 2;
```

## Analysis Approach

Primary analysis done in R/Quarto (in `analysis/` directory). Database accessible via:
- R: `DBI` + `RSQLite`
- Python: `sqlite3` + `pandas`

## XBRL Extraction Notes

- Uses edgartools library for SEC EDGAR access
- Investment identifiers parsed from `dim_us-gaap_InvestmentIdentifierAxis` column
- Format: "Company Name, Industry Sector N" (N = position number)
- Some BDCs have incomplete XBRL tagging (data in HTML tables only)
