#!/usr/bin/env python3
"""
BDC Pipeline: Extract from EDGAR XBRL → Load to SQLite

Uses column-based dimension access from edgartools.
"""

import argparse
import pandas as pd
import sys
import re
from pathlib import Path
from typing import Optional
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from edgar import Company, set_identity
from src.db_loader import BDCDatabase, classify_asset_class
from src.classify_industries import classify_industry

DB_PATH = PROJECT_ROOT / "data" / "bdc_portfolio.db"

AVAILABLE_BDCS = {
    'ARCC': {'cik': 1287750, 'name': 'Ares Capital Corporation'},
    'FSK':  {'cik': 1422183, 'name': 'FS KKR Capital Corp'},
    'BXSL': {'cik': 1736035, 'name': 'Blackstone Secured Lending Fund'},
    'ORCC': {'cik': 1655888, 'name': 'Blue Owl Capital Corp'},
    'GBDC': {'cik': 1476765, 'name': 'Golub Capital BDC Inc'},
    'PSEC': {'cik': 1287032, 'name': 'Prospect Capital Corporation'},
    'MAIN': {'cik': 1396440, 'name': 'Main Street Capital Corporation'},
    'HTGC': {'cik': 1280784, 'name': 'Hercules Capital Inc'},
    'NMFC': {'cik': 1496099, 'name': 'New Mountain Finance Corporation'},
    'OCSL': {'cik': 1414932, 'name': 'Oaktree Specialty Lending Corporation'},
    'TPVG': {'cik': 1580345, 'name': 'TriplePoint Venture Growth BDC Corp'},
    'TRIN': {'cik': 1760542, 'name': 'Trinity Capital Inc'},
    'CSWC': {'cik': 18349,   'name': 'Capital Southwest Corporation'},
    'GLAD': {'cik': 1284812, 'name': 'Gladstone Capital Corporation'},
    'GAIN': {'cik': 1284806, 'name': 'Gladstone Investment Corporation'},
    'FDUS': {'cik': 1487918, 'name': 'Fidus Investment Corporation'},
    'PNNT': {'cik': 1417286, 'name': 'PennantPark Floating Rate Capital Ltd'},
    'PFLT': {'cik': 1418076, 'name': 'PennantPark Floating Rate Capital Ltd'},
    'SLRC': {'cik': 1468174, 'name': 'SLR Investment Corp'},
    'TCPC': {'cik': 1393881, 'name': 'BlackRock TCP Capital Corp'},
}

# BDCs we'll test - expand as we confirm they work
XBRL_COMPLIANT_BDCS = ['ARCC', 'FSK', 'PSEC', 'MAIN', 'NMFC', 'OCSL', 'CSWC', 'GLAD', 'GAIN', 'FDUS']

# Concepts we want to extract
TARGET_CONCEPTS = [
    'us-gaap:InvestmentOwnedAtFairValue',
    'us-gaap:InvestmentOwnedAtCost', 
    'us-gaap:InvestmentOwnedBalancePrincipalAmount',
    'us-gaap:InvestmentOwnedBalanceShares',
    'us-gaap:InvestmentBasisSpreadVariableRate',
    'us-gaap:InvestmentInterestRate',
    'us-gaap:InvestmentInterestRateFloor',
]

DEBT_KEYWORDS = ['loan', 'debt', 'note', 'bond', 'credit', 'mezzanine', 
                 'senior', 'subordinated', 'unitranche', 'secured', 'first lien', 'second lien']
EQUITY_KEYWORDS = ['stock', 'equity', 'share', 'warrant', 'option', 'unit',
                   'membership', 'partnership', 'llc', 'lp', 'preferred', 'common']


def parse_investment_identifier(inv_id: str) -> dict:
    """
    Parse investment identifier like '3Pillar Global Inc, Software & Services 1'
    Returns dict with company_name, industry, position_num
    """
    if not inv_id or pd.isna(inv_id):
        return {'company_name': 'Unknown', 'industry': None, 'position_num': None}
    
    # Pattern: "Company Name, Industry Sector N" or just "Company Name N"
    # The number at the end distinguishes multiple positions in same company
    
    # Try to extract trailing number
    match = re.match(r'^(.+?)\s+(\d+)$', inv_id.strip())
    if match:
        base = match.group(1)
        position_num = int(match.group(2))
    else:
        base = inv_id.strip()
        position_num = 1
    
    # Try to split on comma for company, industry
    if ', ' in base:
        parts = base.rsplit(', ', 1)
        company_name = parts[0].strip()
        industry = parts[1].strip() if len(parts) > 1 else None
    else:
        company_name = base
        industry = None
    
    return {
        'company_name': company_name,
        'industry': industry,
        'position_num': position_num
    }


def classify_from_identifier(inv_id: str) -> str:
    """Classify as Debt/Equity based on identifier text."""
    if not inv_id:
        return 'Unknown'
    
    inv_lower = inv_id.lower()
    
    for kw in DEBT_KEYWORDS:
        if kw in inv_lower:
            return 'Debt'
    for kw in EQUITY_KEYWORDS:
        if kw in inv_lower:
            return 'Equity'
    
    return 'Unknown'


def extract_investments_from_xbrl(xbrl) -> pd.DataFrame:
    """
    Extract investments from XBRL using column-based dimension access.
    """
    try:
        all_facts = xbrl.facts.to_dataframe()
    except Exception as e:
        print(f"    Error getting facts: {e}")
        return pd.DataFrame()
    
    # Find the InvestmentIdentifierAxis column
    inv_id_col = None
    for col in all_facts.columns:
        if 'InvestmentIdentifierAxis' in col:
            inv_id_col = col
            break
    
    if not inv_id_col:
        print(f"    No InvestmentIdentifierAxis column found")
        return pd.DataFrame()
    
    # Filter to facts with investment identifiers
    inv_facts = all_facts[all_facts[inv_id_col].notna()].copy()
    
    if inv_facts.empty:
        print(f"    No facts with InvestmentIdentifierAxis")
        return pd.DataFrame()
    
    print(f"    Found {len(inv_facts)} investment facts")
    
    # Pivot: group by investment identifier and collect values for each concept
    investments = defaultdict(dict)
    
    for _, row in inv_facts.iterrows():
        inv_id = row[inv_id_col]
        concept = row['concept']
        value = row['value']
        
        # Store the value
        if 'FairValue' in concept:
            investments[inv_id]['fair_value'] = value
        elif 'AtCost' in concept:
            investments[inv_id]['cost'] = value
        elif 'PrincipalAmount' in concept:
            investments[inv_id]['principal'] = value
        elif 'Shares' in concept:
            investments[inv_id]['shares'] = value
        elif 'SpreadVariableRate' in concept:
            investments[inv_id]['spread'] = value
        elif 'InterestRate' in concept and 'Floor' not in concept:
            investments[inv_id]['interest_rate'] = value
        
        # Store period_end from any fact
        if 'period_end' not in investments[inv_id]:
            investments[inv_id]['period_end'] = row.get('period_end') or row.get('period_instant')
    
    if not investments:
        return pd.DataFrame()
    
    # Convert to DataFrame
    records = []
    for inv_id, data in investments.items():
        parsed = parse_investment_identifier(inv_id)
        
        # Determine asset class
        has_principal = pd.notna(data.get('principal'))
        has_shares = pd.notna(data.get('shares'))
        
        if has_principal and not has_shares:
            asset_class = 'Debt'
        elif has_shares and not has_principal:
            asset_class = 'Equity'
        else:
            asset_class = classify_from_identifier(inv_id)
        
        records.append({
            'investment_id': inv_id,
            'company_name': parsed['company_name'],
            'industry': parsed['industry'],
            'position_num': parsed['position_num'],
            'fair_value': data.get('fair_value'),
            'cost': data.get('cost'),
            'principal': data.get('principal'),
            'shares': data.get('shares'),
            'spread': data.get('spread'),
            'interest_rate': data.get('interest_rate'),
            'asset_class': asset_class,
            'period_end': data.get('period_end'),
        })
    
    return pd.DataFrame(records)


def get_bdc_10k(ticker: str, year: Optional[int] = None, amendments: bool = False):
    """Get 10-K filing, optionally excluding amendments."""
    company = Company(ticker)
    filings = company.get_filings(form="10-K", amendments=amendments)
    
    if not filings or len(filings) == 0:
        # Try with amendments if none found
        if not amendments:
            return get_bdc_10k(ticker, year, amendments=True)
        raise ValueError(f"No 10-K filings found for {ticker}")
    
    if year:
        for f in filings:
            filing_year = f.filing_date.year
            fiscal_year = filing_year - 1 if f.filing_date.month <= 4 else filing_year
            if fiscal_year == year:
                return f
        raise ValueError(f"No 10-K found for {ticker} fiscal year {year}")
    
    return filings.latest()


def derive_period_end(filing, year: Optional[int] = None) -> str:
    """Derive period end date."""
    if year:
        return f"{year}-12-31"
    
    filing_year = filing.filing_date.year
    if filing.filing_date.month <= 4:
        return f"{filing_year - 1}-12-31"
    return f"{filing_year}-12-31"


def extract_and_load_bdc(ticker: str, db: BDCDatabase, year: Optional[int] = None) -> dict:
    """Extract and load a BDC."""
    
    if ticker not in AVAILABLE_BDCS:
        return {'ticker': ticker, 'year': year, 'status': 'error', 'message': 'Unknown ticker'}
    
    bdc_info = AVAILABLE_BDCS[ticker]
    year_str = str(year) if year else "latest"
    
    print(f"\n{'='*60}")
    print(f"{ticker} - {bdc_info['name']} ({year_str})")
    print(f"{'='*60}")
    
    stats = {
        'ticker': ticker,
        'name': bdc_info['name'],
        'year': year,
        'status': 'pending',
        'holdings_extracted': 0,
        'investments_loaded': 0,
    }
    
    try:
        # Get filing (prefer non-amendments)
        print(f"  Fetching 10-K...")
        filing = get_bdc_10k(ticker, year, amendments=False)
        print(f"  Filing: {filing.accession_number} ({filing.filing_date}) [{filing.form}]")
        
        period_end = derive_period_end(filing, year)
        stats['period_end'] = period_end
        stats['filing_date'] = str(filing.filing_date)
        
        # Parse XBRL
        print(f"  Parsing XBRL...")
        xbrl = filing.xbrl()
        if not xbrl:
            stats['status'] = 'error'
            stats['message'] = 'No XBRL data'
            return stats
        
        # Extract investments
        print(f"  Extracting investments...")
        investments_df = extract_investments_from_xbrl(xbrl)
        
        if investments_df.empty:
            stats['status'] = 'no_data'
            stats['message'] = 'No investments extracted'
            return stats
        
        stats['holdings_extracted'] = len(investments_df)
        print(f"  ✓ Extracted {len(investments_df)} investments")
        
        # Load to database
        print(f"  Loading to database (period: {period_end})...")
        
        bdc_ticker = db.get_or_create_bdc(
            name=bdc_info['name'],
            cik=str(bdc_info['cik'])
        )
        
        loaded = 0
        for _, row in investments_df.iterrows():
            company_id = db.get_or_create_company(
                name=row['company_name'],
                business_desc=None,
                industry_sector=row.get('industry')
            )
            
            # Determine investment type from identifier
            inv_type = None
            if row['asset_class'] == 'Debt':
                inv_type = 'Senior Secured Loan'  # Default
            elif row['asset_class'] == 'Equity':
                inv_type = 'Equity'
            
            inv_id = db.add_investment(
                bdc_ticker=bdc_ticker,
                company_id=company_id,
                investment_type=inv_type,
                fair_value=row.get('fair_value'),
                cost=row.get('cost'),
                principal=row.get('principal'),
                period_end=period_end
            )
            
            if inv_id:
                loaded += 1
        
        stats['investments_loaded'] = loaded
        stats['status'] = 'success'
        print(f"  ✓ Loaded {loaded} investments")
        
    except Exception as e:
        stats['status'] = 'error'
        stats['message'] = str(e)
        print(f"  ✗ Error: {e}")
    
    return stats


def show_available_bdcs():
    print("\nAvailable BDCs:")
    print("-" * 70)
    for ticker, info in sorted(AVAILABLE_BDCS.items()):
        compliant = "✓" if ticker in XBRL_COMPLIANT_BDCS else "?"
        print(f"  {ticker:<8} {info['name']:<45} {compliant}")
    print(f"\nTotal: {len(AVAILABLE_BDCS)} BDCs")


def show_database_status(db: BDCDatabase):
    print("\nDatabase Status:")
    print("-" * 60)
    
    summary = db.get_bdc_summary()
    if summary.empty:
        print("  No data loaded yet.")
        return
    
    print(f"\nLoaded: {summary['bdc_ticker'].nunique()} BDCs across {summary['period_end'].nunique()} periods")
    print(summary.to_string(index=False))
    
    overlap = db.get_overlap_summary()
    print(f"\nOverlap companies (held by 2+ BDCs): {len(overlap)}")


def main():
    parser = argparse.ArgumentParser(description="BDC Pipeline: EDGAR XBRL → SQLite")
    parser.add_argument('--tickers', nargs='+', help='BDC tickers')
    parser.add_argument('--years', nargs='+', type=int, help='Fiscal years')
    parser.add_argument('--list', action='store_true', help='List BDCs')
    parser.add_argument('--status', action='store_true', help='Show status')
    parser.add_argument('--compliant', action='store_true', help='Process compliant BDCs')
    parser.add_argument('--db', type=Path, default=DB_PATH)
    parser.add_argument('--reset', action='store_true', help='Reset database')
    args = parser.parse_args()
    
    set_identity("BDC Analysis Project research@example.com")
    
    if args.list:
        show_available_bdcs()
        return
    
    print("=" * 60)
    print("BDC Pipeline: EDGAR XBRL → SQLite")
    print("=" * 60)
    
    if args.reset and args.db.exists():
        print(f"Removing: {args.db}")
        args.db.unlink()
    
    with BDCDatabase(args.db) as db:
        db.init_schema()
        
        if args.status:
            show_database_status(db)
            return
        
        if args.tickers:
            tickers = [t.upper() for t in args.tickers]
        elif args.compliant:
            tickers = XBRL_COMPLIANT_BDCS.copy()
        else:
            show_database_status(db)
            print("\nUsage:")
            print("  --tickers ARCC FSK")
            print("  --tickers ARCC --years 2022 2023 2024")
            print("  --compliant --years 2022 2023 2024")
            return
        
        years = args.years if args.years else [None]
        
        results = []
        total = len(tickers) * len(years)
        
        for i, ticker in enumerate(tickers):
            for j, year in enumerate(years):
                current = i * len(years) + j + 1
                print(f"\n[{current}/{total}]")
                stats = extract_and_load_bdc(ticker, db, year=year)
                results.append(stats)
        
        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        
        success = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] != 'success']
        
        print(f"\nProcessed: {len(results)}")
        print(f"  ✓ Success: {len(success)}")
        print(f"  ✗ Failed:  {len(failed)}")
        
        if success:
            print(f"\nSuccessful:")
            for r in success:
                yr = str(r['year']) if r['year'] else "latest"
                print(f"  {r['ticker']} ({yr}): {r['holdings_extracted']} → {r['investments_loaded']}")
        
        if failed:
            print(f"\nFailed:")
            for r in failed:
                yr = str(r['year']) if r['year'] else "latest"
                print(f"  {r['ticker']} ({yr}): {r.get('message', r['status'])}")
        
        print("\n" + "-" * 60)
        show_database_status(db)


if __name__ == "__main__":
    main()
