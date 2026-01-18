#!/usr/bin/env python3
"""
BDC Portfolio Database Loader

Initializes SQLite database and loads existing CSV extracts.
Handles entity resolution for portfolio companies across BDCs.

Usage:
    python db_loader.py                    # Initialize and load all data
    python db_loader.py --schema-only      # Just create tables
    python db_loader.py --csv path/to/csv  # Load specific CSV
"""

import sqlite3
import pandas as pd
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

# Configuration - paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "bdc_portfolio.db"
SCHEMA_PATH = PROJECT_ROOT / "db" / "schema.sql"
DEFAULT_CSV = PROJECT_ROOT / "outputs" / "all_bdc_holdings_with_industry.csv"


def normalize_company_name(name: str) -> str:
    """
    Normalize company name for matching.
    
    Strategy: Conservative normalization to avoid false positives.
    - Lowercase
    - Remove common suffixes (Inc, LLC, LP, Corp, etc.)
    - Remove parenthetical notes like "(4)" or "(Delaware)"
    - Collapse whitespace
    
    Does NOT do aggressive fuzzy matching - that's Phase 2.
    """
    if not name or pd.isna(name):
        return ""
    
    # Lowercase
    normalized = name.lower().strip()
    
    # Remove parenthetical notes at end: "(4)", "(Delaware)", etc.
    normalized = re.sub(r'\s*\([^)]*\)\s*$', '', normalized)
    
    # Remove common legal suffixes
    suffixes = [
        r',?\s+inc\.?$',
        r',?\s+llc\.?$',
        r',?\s+l\.?l\.?c\.?$',
        r',?\s+lp\.?$',
        r',?\s+l\.?p\.?$',
        r',?\s+corp\.?$',
        r',?\s+corporation$',
        r',?\s+company$',
        r',?\s+co\.?$',
        r',?\s+ltd\.?$',
        r',?\s+limited$',
        r',?\s+holdings?$',
        r',?\s+intermediate$',
        r',?\s+parent$',
        r',?\s+bidco$',
        r',?\s+topco$',
    ]
    
    for suffix in suffixes:
        normalized = re.sub(suffix, '', normalized, flags=re.IGNORECASE)
    
    # Collapse multiple spaces
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized


def classify_asset_class(investment_type: str) -> str:
    """Derive asset class from investment type."""
    if not investment_type or pd.isna(investment_type):
        return "Unknown"
    
    inv_lower = investment_type.lower()
    
    debt_keywords = ['loan', 'debt', 'secured', 'subordinated', 'mezzanine', 
                     'note', 'bond', 'credit', 'unitranche']
    equity_keywords = ['stock', 'equity', 'share', 'unit', 'warrant', 
                       'preferred', 'common', 'membership', 'partnership', 'llc', 'lp']
    
    for kw in debt_keywords:
        if kw in inv_lower:
            return "Debt"
    
    for kw in equity_keywords:
        if kw in inv_lower:
            return "Equity"
    
    return "Unknown"


def map_industry_to_code(industry_name: str) -> str:
    """Map industry sector string to our standard codes."""
    if not industry_name or pd.isna(industry_name):
        return None
    
    mapping = {
        'software/technology': 'SOFTWARE',
        'software': 'SOFTWARE',
        'technology': 'SOFTWARE',
        'healthcare': 'HEALTHCARE',
        'healthcare services': 'HEALTHCARE_SERVICES',
        'business services': 'BUSINESS_SERVICES',
        'financial services': 'FINANCIAL_SERVICES',
        'consumer products': 'CONSUMER',
        'consumer services': 'CONSUMER_SERVICES',
        'consumer': 'CONSUMER',
        'industrial/manufacturing': 'INDUSTRIAL',
        'industrial': 'INDUSTRIAL',
        'manufacturing': 'INDUSTRIAL',
        'transportation & logistics': 'TRANSPORTATION',
        'transportation': 'TRANSPORTATION',
        'logistics': 'TRANSPORTATION',
        'energy': 'ENERGY',
        'media & entertainment': 'MEDIA',
        'media': 'MEDIA',
        'entertainment': 'MEDIA',
        'telecommunications': 'TELECOM',
        'real estate': 'REAL_ESTATE',
        'education': 'EDUCATION',
        'government services': 'GOVERNMENT',
    }
    
    industry_lower = industry_name.lower().strip()
    return mapping.get(industry_lower, 'OTHER')


class BDCDatabase:
    """SQLite database handler for BDC portfolio analysis."""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        
    def connect(self):
        """Open database connection."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        # Enable foreign keys
        self.conn.execute("PRAGMA foreign_keys = ON")
        return self
        
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            
    def __enter__(self):
        return self.connect()
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        
    def init_schema(self, schema_path: Path = SCHEMA_PATH):
        """Create tables from schema file."""
        with open(schema_path) as f:
            schema_sql = f.read()
        
        self.conn.executescript(schema_sql)
        self.conn.commit()
        print(f"✓ Schema initialized: {self.db_path}")
        
    def get_or_create_bdc(self, name: str, cik: str = None) -> str:
        """Get or create BDC record, return ticker."""
        cursor = self.conn.cursor()
        
        # Check if exists by CIK
        if cik:
            cursor.execute("SELECT ticker FROM bdc WHERE cik = ?", (cik,))
            row = cursor.fetchone()
            if row:
                return row['ticker']
        
        # Check by name
        cursor.execute("SELECT ticker FROM bdc WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            return row['ticker']
        
        # Create new - use abbreviated ticker from name
        ticker = self._derive_ticker(name)
        cursor.execute(
            "INSERT INTO bdc (ticker, name, cik) VALUES (?, ?, ?)",
            (ticker, name, cik)
        )
        self.conn.commit()
        print(f"  Created BDC: {ticker} ({name})")
        return ticker
    
    def _derive_ticker(self, name: str) -> str:
        """Derive a ticker symbol from BDC name."""
        ticker_map = {
            'ares capital': 'ARCC',
            'main street capital': 'MAIN',
            'hercules capital': 'HTGC',
            'fs kkr capital': 'FSK',
            'blue owl capital': 'OBDC',
            'golub capital': 'GBDC',
            'owl rock': 'ORCC',
            'prospect capital': 'PSEC',
            'trinity capital': 'TRIN',
            'blackstone secured': 'BXSL',
        }
        
        name_lower = name.lower()
        for key, ticker in ticker_map.items():
            if key in name_lower:
                return ticker
        
        # Fallback: first letters of words
        words = name.split()[:4]
        return ''.join(w[0].upper() for w in words if w)
    
    def get_or_create_company(
        self, 
        name: str, 
        business_desc: str = None,
        industry_sector: str = None
    ) -> int:
        """Get or create portfolio company, return ID."""
        cursor = self.conn.cursor()
        
        normalized = normalize_company_name(name)
        
        # Check if exists
        cursor.execute(
            "SELECT id FROM portfolio_company WHERE normalized_name = ?",
            (normalized,)
        )
        row = cursor.fetchone()
        if row:
            # Update business_desc if we have new info
            if business_desc and not pd.isna(business_desc):
                cursor.execute(
                    """UPDATE portfolio_company 
                       SET business_desc = COALESCE(business_desc, ?),
                           updated_at = CURRENT_TIMESTAMP
                       WHERE id = ?""",
                    (business_desc, row['id'])
                )
            return row['id']
        
        # Create new
        industry_code = map_industry_to_code(industry_sector)
        cursor.execute(
            """INSERT INTO portfolio_company 
               (normalized_name, business_desc, assigned_industry, classification_method)
               VALUES (?, ?, ?, ?)""",
            (normalized, business_desc, industry_code, 'KEYWORD' if industry_code else None)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def add_investment(
        self,
        bdc_ticker: str,
        company_id: int,
        investment_type: str,
        fair_value: float,
        cost: float = None,
        principal: float = None,
        period_end: str = None,
        **kwargs
    ) -> Optional[int]:
        """
        Add or update investment position.
        
        Uses (bdc_ticker, company_id, investment_type, period_end) as business key.
        - If identical record exists: skip (return None)
        - If record exists with different values: update (return existing ID)
        - If new record: insert (return new ID)
        
        Returns:
            int: Investment ID (new or updated)
            None: If skipped (identical record exists)
        """
        cursor = self.conn.cursor()
        
        asset_class = classify_asset_class(investment_type)
        
        # Default period_end
        if not period_end:
            period_end = "2024-12-31"
        
        # Check if this position already exists for this period
        cursor.execute(
            """SELECT id, fair_value, cost, principal FROM investment 
               WHERE bdc_ticker = ? AND company_id = ? 
               AND COALESCE(investment_type, '') = COALESCE(?, '')
               AND period_end = ?""",
            (bdc_ticker, company_id, investment_type, period_end)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Already exists - check if values changed
            existing_fv = existing['fair_value']
            existing_cost = existing['cost']
            existing_principal = existing['principal']
            
            # Compare (handle None/NULL)
            values_match = (
                (existing_fv == fair_value or (existing_fv is None and fair_value is None)) and
                (existing_cost == cost or (existing_cost is None and cost is None)) and
                (existing_principal == principal or (existing_principal is None and principal is None))
            )
            
            if values_match:
                # Identical - skip
                return None
            else:
                # Values changed - update
                cursor.execute(
                    """UPDATE investment 
                       SET fair_value = ?, cost = ?, principal = ?, asset_class = ?
                       WHERE id = ?""",
                    (fair_value, cost, principal, asset_class, existing['id'])
                )
                self.conn.commit()
                return existing['id']
        else:
            # New position - insert
            try:
                cursor.execute(
                    """INSERT INTO investment 
                       (bdc_ticker, company_id, investment_type, asset_class,
                        fair_value, cost, principal, period_end)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (bdc_ticker, company_id, investment_type, asset_class,
                     fair_value, cost, principal, period_end)
                )
                self.conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                # Race condition or constraint violation - skip
                return None
    
    def load_from_csv(self, csv_path: Path, period_end: str = "2024-09-30"):
        """Load holdings from CSV extract."""
        print(f"\nLoading: {csv_path}")
        
        df = pd.read_csv(csv_path)
        print(f"  Rows: {len(df):,}")
        
        # Track stats
        stats = {
            'bdcs': set(),
            'companies': set(),
            'investments': 0,
            'duplicates': 0,
            'updated': 0,
        }
        
        for _, row in df.iterrows():
            # Get or create BDC
            bdc_ticker = self.get_or_create_bdc(
                name=row['bdc_name'],
                cik=str(row['bdc_cik']) if pd.notna(row.get('bdc_cik')) else None
            )
            stats['bdcs'].add(bdc_ticker)
            
            # Get or create company
            company_id = self.get_or_create_company(
                name=row['company_name'],
                business_desc=row.get('business_description'),
                industry_sector=row.get('industry_sector')
            )
            stats['companies'].add(company_id)
            
            # Add investment
            inv_id = self.add_investment(
                bdc_ticker=bdc_ticker,
                company_id=company_id,
                investment_type=row.get('investment_type'),
                fair_value=row.get('fair_value'),
                cost=row.get('cost'),
                principal=row.get('principal'),
                period_end=period_end
            )
            
            if inv_id:
                stats['investments'] += 1
            else:
                stats['duplicates'] += 1
        
        print(f"\n  Summary:")
        print(f"    BDCs: {len(stats['bdcs'])}")
        print(f"    Companies: {len(stats['companies'])}")
        print(f"    Investments: {stats['investments']:,}")
        print(f"    Duplicates skipped: {stats['duplicates']:,}")
        
        return stats
    
    def get_overlap_summary(self) -> pd.DataFrame:
        """Query companies held by multiple BDCs."""
        query = """
            SELECT * FROM v_overlap_companies
            ORDER BY bdc_count DESC, total_fair_value DESC
        """
        return pd.read_sql_query(query, self.conn)
    
    def get_industry_concentration(self, bdc_ticker: str = None) -> pd.DataFrame:
        """Query industry concentration."""
        query = "SELECT * FROM v_industry_concentration"
        if bdc_ticker:
            query += f" WHERE bdc_ticker = '{bdc_ticker}'"
        query += " ORDER BY total_fair_value DESC"
        return pd.read_sql_query(query, self.conn)
    
    def get_bdc_summary(self) -> pd.DataFrame:
        """Get summary stats for all BDCs."""
        return pd.read_sql_query("SELECT * FROM v_bdc_summary", self.conn)


def main():
    parser = argparse.ArgumentParser(description="BDC Portfolio Database Loader")
    parser.add_argument('--schema-only', action='store_true', 
                        help='Only create schema, no data load')
    parser.add_argument('--csv', type=Path, default=DEFAULT_CSV,
                        help='Path to CSV file to load')
    parser.add_argument('--db', type=Path, default=DB_PATH,
                        help='Database path')
    parser.add_argument('--period', type=str, default="2024-09-30",
                        help='Period end date for the data (YYYY-MM-DD)')
    args = parser.parse_args()
    
    print("=" * 60)
    print("BDC Portfolio Database Loader")
    print("=" * 60)
    
    with BDCDatabase(args.db) as db:
        # Initialize schema
        db.init_schema()
        
        if args.schema_only:
            print("\nSchema created. Use --csv to load data.")
            return
        
        # Load data
        if args.csv.exists():
            db.load_from_csv(args.csv, period_end=args.period)
        else:
            print(f"\nWarning: CSV not found: {args.csv}")
            print("Database initialized but no data loaded.")
            return
        
        # Show summary
        print("\n" + "=" * 60)
        print("Database Summary")
        print("=" * 60)
        
        summary = db.get_bdc_summary()
        if not summary.empty:
            print("\nBDC Summary:")
            print(summary.to_string(index=False))
        
        overlap = db.get_overlap_summary()
        if not overlap.empty:
            print(f"\nOverlap Companies (held by 2+ BDCs): {len(overlap)}")
            print(overlap.head(10).to_string(index=False))
        else:
            print("\nNo overlap companies found (companies held by multiple BDCs)")


if __name__ == "__main__":
    main()
