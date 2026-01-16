# BDC Data Download Issue

**Date:** 2026-01-15
**Status:** URL Not Working

## Problem

The SEC BDC Data Set download URL from the planning document is returning a 404 error:

```
https://www.sec.gov/files/dera/data/bdc-data-sets/bdc-data-sets.zip
```

Alternative URL patterns also return 404:
- `https://www.sec.gov/dera/data/bdc-data-sets.zip`

## SEC Page Status

The official SEC BDC Data Sets page exists at:
- https://www.sec.gov/data-research/sec-markets-data/bdc-data-sets

However, this page is blocking automated access (403 Forbidden) and web scraping attempts.

## Possible Solutions

### Option 1: Manual Download
1. Visit https://www.sec.gov/data-research/sec-markets-data/bdc-data-sets in a web browser
2. Locate and download the BDC data ZIP file manually
3. Extract to `data/raw/bdc-data-sets/`
4. Run profiling: `python3 -m src.profile`

### Option 2: Check data.gov Catalog
The data is also listed on data.gov:
- https://catalog.data.gov/dataset/business-development-company-bdc-data-sets

This may provide alternative download links or APIs.

### Option 3: Use EDGAR API Directly
Access BDC filings directly through SEC EDGAR:
- Download individual 10-K/10-Q filings
- Parse Schedule of Investments from each filing
- More work but guaranteed access

### Option 4: Alternative Data Sources
- Bloomberg Terminal (if available)
- FactSet or other financial data providers
- Direct from BDC investor relations websites

## Recommended Next Steps

1. **Try manual download first** - Visit the SEC page in a browser and see if the download link is available
2. **Check SEC's robots.txt** - Ensure we're complying with their crawler policies
3. **Contact SEC** - If data is no longer available in bulk format, may need to file a data request
4. **Update download.py** - Once we find the working URL or method, update the code

## Sources

- [SEC BDC Data Sets](https://www.sec.gov/data-research/sec-markets-data/bdc-data-sets)
- [SEC BDC Data Sets Announcement](https://www.sec.gov/newsroom/whats-new/2506-bdc-data-sets)
- [data.gov - BDC Data Sets](https://catalog.data.gov/dataset/business-development-company-bdc-data-sets)
