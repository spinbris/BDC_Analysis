# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

**BDC Portfolio Overlap Analysis** - Analyzes overlapping portfolio holdings across major Business Development Companies (BDCs) to assess concentration risk in the private credit market.

**Research Context:** BDCs represent ~$450B of the $2T+ private credit market and are uniquely transparent - they file detailed Schedule of Investments with the SEC. This project maps common exposures that could transmit stress across the sector.

## Repository Structure

```
BDC_Analysis/
├── CLAUDE.md                    # This file (Claude Code reads automatically)
├── Docs/
│   └── PLANNING.md              # Master planning document - READ THIS FIRST
├── data/
│   ├── raw/                     # Downloaded SEC BDC Data Sets
│   └── processed/               # Cleaned/normalized data
├── src/
│   ├── __init__.py
│   ├── download.py              # SEC data acquisition
│   ├── load.py                  # Data loading and filtering
│   ├── normalize.py             # Entity resolution (identifiers → fuzzy)
│   ├── overlap.py               # Overlap analysis calculations
│   └── export.py                # Excel/visualization output
├── outputs/                     # Analysis results
├── tests/
├── requirements.txt
└── pyproject.toml
```

## Getting Started

```bash
# Setup virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Create data directories
mkdir -p data/raw data/processed outputs
```

## Implementation Plan

**See `Docs/PLANNING.md` for the full phased implementation plan.**

Quick summary:
- **Phase 1:** Prototype - Download data, profile for identifiers, basic overlap
- **Phase 2:** Entity Resolution - Identifiers first, fuzzy matching as fallback
- **Phase 3:** Rich Analysis - Full metrics and exposure quantification
- **Phase 4:** Historical - Time series analysis
- **Phase 5:** Reporting - Final outputs and visualizations

## Entity Matching Strategy

**Priority order (identifiers first, fuzzy last):**

| Priority | Method | When to Use |
|----------|--------|-------------|
| 1 | Exact identifier (CUSIP/LEI/CIK) | If present in data |
| 2 | Exact name match | Quick wins, no ambiguity |
| 3 | Normalized name match | Same name, different formatting |
| 4 | Fuzzy match | Only for remaining unmatched |

## Data Source

**SEC BDC Data Sets:** https://www.sec.gov/data-research/sec-markets-data/bdc-data-sets

Key files in the ZIP:
- `soi.tsv` - Schedule of Investments (position-level holdings)
- `sub.tsv` - Submission metadata (BDC identifiers, filing dates)

SEC requires User-Agent header for downloads - use project identity.

## Target BDCs (Top 10 by Fair Value)

| Ticker | CIK | Name | ~Fair Value |
|--------|-----|------|-------------|
| ARCC | 1287750 | Ares Capital Corporation | $26B |
| FSK | 1631115 | FS KKR Capital Corp | $15B |
| BXSL | 1838831 | Blackstone Secured Lending Fund | $13B |
| ORCC | 1758190 | Blue Owl Capital Corporation | $13B |
| GBDC | 1476765 | Golub Capital BDC Inc | $8B |
| PSEC | 1287032 | Prospect Capital Corporation | $7B |
| MAIN | 1396440 | Main Street Capital Corporation | $7B |
| HTGC | 1280784 | Hercules Capital Inc | $3.5B |
| NMFC | 1496099 | New Mountain Finance Corporation | $3B |
| OCSL | 1414932 | Oaktree Specialty Lending Corporation | $3B |

## Code Standards

- Python 3.11+
- Type hints for function signatures
- Docstrings for public functions
- Black formatting (line length 88)
- Tests in `tests/` directory

## Key Libraries

- `pandas` - Data manipulation
- `rapidfuzz` - Fuzzy string matching (fallback for entity resolution)
- `openpyxl` - Excel output
- `requests` - SEC data downloads
