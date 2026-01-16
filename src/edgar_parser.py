"""
Parse Schedule of Investments from BDC 10-K HTML filings.

Usage:
    from src.edgar_parser import parse_schedule_of_investments, get_bdc_10k

    filing = get_bdc_10k("ARCC")
    holdings = parse_schedule_of_investments(filing)
"""

import pandas as pd
from bs4 import BeautifulSoup
import re
from typing import Optional, List, Dict
from edgar import Company, set_identity
from io import StringIO


# Corrected CIK mapping for top 10 BDCs
TOP_10_BDCS = {
    1287750: {"ticker": "ARCC", "name": "Ares Capital Corporation"},
    1422183: {"ticker": "FSK",  "name": "FS KKR Capital Corp"},
    1736035: {"ticker": "BXSL", "name": "Blackstone Secured Lending Fund"},
    1655888: {"ticker": "ORCC", "name": "Blue Owl Capital Corp"},
    1476765: {"ticker": "GBDC", "name": "Golub Capital BDC Inc"},
    1287032: {"ticker": "PSEC", "name": "Prospect Capital Corporation"},
    1396440: {"ticker": "MAIN", "name": "Main Street Capital Corporation"},
    1280784: {"ticker": "HTGC", "name": "Hercules Capital Inc"},
    1496099: {"ticker": "NMFC", "name": "New Mountain Finance Corporation"},
    1414932: {"ticker": "OCSL", "name": "Oaktree Specialty Lending Corporation"},
}


def get_bdc_10k(ticker_or_cik: str | int, amendments: bool = False) -> object:
    """Get latest 10-K filing for a BDC.

    Args:
        ticker_or_cik: BDC ticker symbol or CIK number
        amendments: Include amended filings (10-K/A)

    Returns:
        Edgar Filing object
    """
    company = Company(ticker_or_cik)
    filings = company.get_filings(form="10-K", amendments=amendments)
    if len(filings) == 0:
        raise ValueError(f"No 10-K filings found for {ticker_or_cik}")
    return filings[0]


def parse_schedule_of_investments(filing, bdc_name: Optional[str] = None) -> pd.DataFrame:
    """
    Extract Schedule of Investments from a 10-K filing.

    Args:
        filing: Edgar Filing object
        bdc_name: Optional BDC name to add to results

    Returns:
        DataFrame with columns:
        - bdc_name: Name of the BDC (if provided)
        - bdc_cik: CIK of the BDC
        - company_name: Portfolio company name
        - business_description: Business description (if available)
        - investment_type: Type of investment
        - industry: Industry sector (if available)
        - principal: Principal amount
        - cost: Amortized cost
        - fair_value: Fair value
        - pct_net_assets: Percentage of net assets (if available)
    """
    print(f"Parsing Schedule of Investments from {filing.accession_number}...")

    html_content = filing.html()

    # Find position of "Schedule of Investments" in HTML
    soi_pos = html_content.lower().find('schedule of investments')
    if soi_pos == -1:
        print("Warning: 'Schedule of Investments' text not found in HTML")
        soi_pos = 0  # Start from beginning

    print(f"Found 'Schedule of Investments' at position {soi_pos:,}")

    # Extract tables after SOI position
    all_holdings = []

    # Find all table positions after SOI
    table_positions = []
    search_pos = soi_pos

    while True:
        next_table = html_content.lower().find('<table', search_pos)
        if next_table == -1 or next_table > soi_pos + 10000000:  # Within 10MB
            break

        table_end = html_content.lower().find('</table>', next_table)
        if table_end == -1:
            break

        table_html = html_content[next_table:table_end+8]
        table_size = len(table_html)

        # Check if this looks like a SOI table
        # SOI tables typically:
        # - Are large (>50KB)
        # - Contain company name patterns
        # - Have "Fair Value" text

        llc_count = table_html.count('LLC') + table_html.count('Inc.') + table_html.count('Corp.')
        has_fair_value = 'fair value' in table_html.lower()
        has_principal = 'principal' in table_html.lower()

        if table_size > 50000 and llc_count > 5 and (has_fair_value or has_principal):
            table_positions.append({
                'start': next_table,
                'end': table_end,
                'size': table_size,
                'companies': llc_count
            })

        search_pos = table_end + 8

        if len(table_positions) >= 30:  # Check up to 30 tables
            break

    print(f"Found {len(table_positions)} candidate SOI tables")

    # Parse each candidate table
    for i, table_info in enumerate(table_positions):
        print(f"  Parsing table {i+1}/{len(table_positions)} (size: {table_info['size']/1024:.1f}KB, companies: {table_info['companies']})...")

        table_html = html_content[table_info['start']:table_info['end']+8]

        try:
            holdings = extract_holdings_from_table(table_html, filing.cik, bdc_name)
            if holdings:
                all_holdings.extend(holdings)
                print(f"    ✓ Extracted {len(holdings)} holdings")
            else:
                print(f"    ✗ No holdings extracted (likely header/summary table)")
        except Exception as e:
            print(f"    ✗ Error: {e}")

    if not all_holdings:
        print("Warning: No holdings extracted from any tables")
        return pd.DataFrame()

    df = pd.DataFrame(all_holdings)
    print(f"\n✓ Total holdings extracted: {len(df)}")

    return df


def extract_holdings_from_table(table_html: str, bdc_cik: int, bdc_name: Optional[str]) -> List[Dict]:
    """Extract individual holdings from a SOI table.

    Args:
        table_html: HTML content of the table
        bdc_cik: CIK of the BDC
        bdc_name: Name of the BDC

    Returns:
        List of holding dictionaries
    """
    # Parse with pandas
    try:
        df = pd.read_html(StringIO(table_html))[0]
    except Exception as e:
        # If pandas fails, return empty
        return []

    if df.empty or len(df) < 3:  # Need at least header + data
        return []

    holdings = []

    # Find header row (usually row 1, might have "Company" text)
    header_row_idx = None
    for i in range(min(3, len(df))):
        row_text = ' '.join([str(v).lower() for v in df.iloc[i].values if pd.notna(v)])
        if 'company' in row_text and 'fair value' in row_text:
            header_row_idx = i
            break

    if header_row_idx is None:
        # No clear header found
        return []

    # Find key columns in header row
    headers = df.iloc[header_row_idx]

    company_col = None
    business_desc_col = None
    investment_type_col = None
    principal_col = None
    cost_col = None
    fair_value_col = None
    pct_net_assets_col = None

    for i, header in enumerate(headers):
        header_str = str(header).lower()

        # Take FIRST occurrence of each (due to colspan repeats)
        if 'company' in header_str and company_col is None:
            company_col = i
        elif ('business' in header_str or 'description' in header_str) and business_desc_col is None:
            business_desc_col = i
        elif 'investment' in header_str and investment_type_col is None:
            investment_type_col = i
        elif 'principal' in header_str and principal_col is None:
            principal_col = i
        elif ('amortized cost' in header_str or 'cost' in header_str) and cost_col is None:
            cost_col = i
        elif 'fair value' in header_str and fair_value_col is None:
            fair_value_col = i
        elif '% of net assets' in header_str or 'net assets' in header_str:
            if pct_net_assets_col is None:
                pct_net_assets_col = i

    # Detect the scale of values in this table (millions vs thousands)
    # Check median value - if most values are < 1000, likely in millions
    # If most values are > 1000, likely in thousands
    sample_values = []
    for idx in range(header_row_idx + 1, min(header_row_idx + 50, len(df))):
        row = df.iloc[idx]
        for col in [fair_value_col, cost_col, principal_col]:
            if col is not None:
                val = parse_dollar_amount(row.iloc[col])
                if val and val > 0:
                    sample_values.append(val)

    # Determine multiplier based on median
    if sample_values:
        median_val = sorted(sample_values)[len(sample_values) // 2]
        if median_val < 1000:
            value_multiplier = 1_000_000  # Values in millions
        else:
            value_multiplier = 1_000  # Values in thousands
    else:
        value_multiplier = 1_000  # Default to thousands

    # Parse data rows (start after header row)
    # Handle two table formats:
    # Format 1 (ARCC): Each row has company name + investment details
    # Format 2 (MAIN): Company name row, then multiple investment detail rows

    current_company = None
    current_business_desc = None

    for idx in range(header_row_idx + 1, len(df)):
        row = df.iloc[idx]

        if company_col is None:
            continue

        # Get company name from this row
        row_company_name = str(row.iloc[company_col]) if pd.notna(row.iloc[company_col]) else None
        if row_company_name and row_company_name != 'nan' and len(row_company_name) >= 3:
            # Check if it's a section header or total row (skip these)
            skip_patterns = ['total', 'subtotal', 'investments', 'affiliate']
            is_skip_row = any(pattern in row_company_name.lower() for pattern in skip_patterns)

            if not is_skip_row:
                # This row has a company name - might be company header or full data row
                current_company = clean_company_name(row_company_name)

                # Get business description from this row
                if business_desc_col is not None:
                    desc = str(row.iloc[business_desc_col])
                    if desc and desc != 'nan' and len(desc) >= 3:
                        current_business_desc = desc
                    else:
                        current_business_desc = None
                else:
                    current_business_desc = None

        # Now extract investment data from this row
        # (could be same row as company name, or a subsequent detail row)

        # Extract values and apply detected multiplier
        principal = None
        if principal_col is not None:
            principal = parse_dollar_amount(row.iloc[principal_col])
            if principal:
                principal = principal * value_multiplier

        cost = None
        if cost_col is not None:
            cost = parse_dollar_amount(row.iloc[cost_col])
            if cost:
                cost = cost * value_multiplier

        fair_value = None
        if fair_value_col is not None:
            fair_value = parse_dollar_amount(row.iloc[fair_value_col])
            if fair_value:
                fair_value = fair_value * value_multiplier

        # Extract investment type
        investment_type = None
        if investment_type_col is not None:
            inv_type = str(row.iloc[investment_type_col])
            if inv_type and inv_type != 'nan':
                investment_type = inv_type

        # Only create holding record if:
        # 1. We have a current company
        # 2. We have at least one value (to skip empty/header rows)
        # Note: investment_type is optional (not all BDCs have this column)
        has_values = (fair_value is not None or principal is not None or cost is not None)

        if current_company and has_values:
            holdings.append({
                'bdc_name': bdc_name,
                'bdc_cik': bdc_cik,
                'company_name': current_company,
                'business_description': current_business_desc,
                'investment_type': investment_type,
                'principal': principal,
                'cost': cost,
                'fair_value': fair_value,
            })

    return holdings


def parse_dollar_amount(value) -> Optional[float]:
    """Parse a dollar amount from various formats.

    Handles:
    - "$1,234.56"
    - "1234.56"
    - "1,234"
    - "(1,234)" for negatives

    Returns amount in dollars (not millions).
    """
    if value is None or pd.isna(value):
        return None

    value_str = str(value).strip()

    # Remove $ and whitespace
    value_str = value_str.replace('$', '').replace(' ', '').replace(',', '')

    # Handle parentheses (negative)
    is_negative = False
    if value_str.startswith('(') and value_str.endswith(')'):
        is_negative = True
        value_str = value_str[1:-1]

    # Try to convert to float
    try:
        amount = float(value_str)
        if is_negative:
            amount = -amount
        return amount
    except:
        return None


def clean_company_name(name: str) -> str:
    """Clean company name for consistency.

    Removes extra whitespace, standardizes case (keep original),
    and removes common artifacts.
    """
    if not name or not isinstance(name, str):
        return ""

    # Remove extra whitespace
    name = ' '.join(name.split())

    # Remove common footnote markers
    name = re.sub(r'\s*\(\d+\)\s*$', '', name)  # Remove trailing (1), (2), etc.

    return name.strip()


if __name__ == "__main__":
    # Test on ARCC
    set_identity("BDC Analysis Project stephen.parton@example.com")

    print("Testing parser on ARCC...")
    filing = get_bdc_10k("ARCC")
    print(f"Filing: {filing.accession_number} ({filing.filing_date})")

    holdings = parse_schedule_of_investments(filing, bdc_name="Ares Capital Corporation")

    if len(holdings) > 0:
        print(f"\nExtracted {len(holdings)} holdings")
        print("\nFirst 10 holdings:")
        print(holdings.head(10).to_string())

        # Save for inspection
        holdings.to_csv('outputs/arcc_holdings_test.csv', index=False)
        print(f"\nSaved to outputs/arcc_holdings_test.csv")
    else:
        print("\nNo holdings extracted!")
