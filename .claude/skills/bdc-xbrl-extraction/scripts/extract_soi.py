#!/usr/bin/env python3
"""
BDC Schedule of Investments Extractor

Extract portfolio holdings data from BDC 10-K/10-Q filings using XBRL.
Produces separate outputs for debt and equity investments.

Based on ARCC investigation findings (see Docs/ARCC_XBRL_INVESTIGATION_RESULTS.md):
- Investment data is spread across multiple statements (Balance Sheet, SOI, etc.)
- Investment identifiers are in context dimensions (InvestmentIdentifierAxis)
- Each position identified by unique context_ref in xbrl.contexts dictionary

Usage:
    python extract_soi.py ARCC           # Latest 10-K for Ares Capital
    python extract_soi.py MAIN 10-Q      # Latest 10-Q for Main Street Capital
    python extract_soi.py FSK 10-K 2023  # 2023 10-K for FS KKR Capital
    python extract_soi.py ARCC --identity "Your Name email@example.com"

Outputs:
    {TICKER}_debt_investments.csv       # Debt with rate/maturity data
    {TICKER}_equity_investments.csv     # Equity with shares data
    {TICKER}_affiliated_rollforward.csv # Affiliated investment activity
    {TICKER}_portfolio_summary.csv      # Aggregated totals
"""

import sys
import pandas as pd
from collections import defaultdict
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass

# EdgarTools imports
from edgar import Company, set_identity


# ============================================================================
# CONFIGURATION
# ============================================================================

# Debt-specific XBRL concepts (without namespace prefix - normalized during matching)
DEBT_CONCEPTS = {
    'principal': 'InvestmentOwnedBalancePrincipalAmount',
    'interest_rate': 'InvestmentInterestRate',
    'spread': 'InvestmentBasisSpreadVariableRate',
    'floor': 'InvestmentInterestRateFloor',
    'pik_rate': 'InvestmentInterestRatePaidInKind',
    'cash_rate': 'InvestmentInterestRatePaidInCash',
    'maturity_date': 'InvestmentMaturityDate',
    'rate_type': 'InvestmentVariableInterestRateTypeExtensibleEnumeration',
}

# Equity-specific XBRL concepts (without namespace prefix - normalized during matching)
EQUITY_CONCEPTS = {
    'shares': 'InvestmentOwnedBalanceShares',
}

# Common concepts (both debt and equity) - without namespace prefix
COMMON_CONCEPTS = {
    'fair_value': 'InvestmentOwnedAtFairValue',
    'cost': 'InvestmentOwnedAtCost',
    'pct_net_assets': 'InvestmentOwnedPercentOfNetAssets',
    'acquisition_date': 'InvestmentAcquisitionDate',
    'issuer_name': 'InvestmentIssuerNameExtensibleEnumeration',
    'investment_type': 'InvestmentTypeExtensibleEnumeration',
    'industry': 'InvestmentIndustrySectorExtensibleEnumeration',
    'affiliation': 'InvestmentIssuerAffiliationExtensibleEnumeration',
    'is_restricted': 'InvestmentRestrictionStatus',
    'is_level3': 'InvestmentSignificantUnobservableInput',
    'is_non_income': 'InvestmentNonIncomeProducing',
}

# Affiliated roll-forward concepts (without namespace prefix - normalized during matching)
AFFILIATED_CONCEPTS = {
    'gross_additions': 'InvestmentsInAndAdvancesToAffiliatesAtFairValueGrossAdditions',
    'gross_reductions': 'InvestmentsInAndAdvancesToAffiliatesAtFairValueGrossReductions',
    'realized_gain_loss': 'DebtAndEquitySecuritiesRealizedGainLoss',
    'unrealized_gain_loss': 'DebtAndEquitySecuritiesUnrealizedGainLoss',
    'interest_income': 'InterestIncomeOperating',
    'dividend_income': 'DividendIncomeOperating',
}

# Investment types that indicate DEBT
DEBT_TYPE_KEYWORDS = [
    'loan', 'debt', 'note', 'bond', 'credit', 'mezzanine', 
    'senior', 'subordinated', 'unitranche', 'tranche',
    'secured', 'unsecured', 'term', 'revolver', 'revolving'
]

# Investment types that indicate EQUITY
EQUITY_TYPE_KEYWORDS = [
    'stock', 'equity', 'share', 'warrant', 'option', 'unit',
    'membership', 'partnership', 'llc', 'lp', 'preferred',
    'common', 'class a', 'class b'
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def normalize_concept(concept: str) -> str:
    """
    Normalize XBRL concept name by stripping namespace prefix.

    This makes matching more robust across different filings that may or may not
    include namespace prefixes (e.g., "us-gaap:", "dei:", "arcc:").

    Examples:
        "us-gaap:InvestmentOwnedAtFairValue" -> "InvestmentOwnedAtFairValue"
        "arcc:InvestmentCompanyFundedCommitments" -> "InvestmentCompanyFundedCommitments"
        "InvestmentOwnedAtCost" -> "InvestmentOwnedAtCost"

    Args:
        concept: XBRL concept name (with or without namespace prefix)

    Returns:
        Concept name without namespace prefix
    """
    if not concept or not isinstance(concept, str):
        return concept

    # Split on colon and take the last part (after namespace prefix)
    if ':' in concept:
        return concept.split(':', 1)[1]

    return concept


def parse_enum_uri(uri: str) -> str:
    """Parse extensible enumeration URI to extract readable value."""
    if not uri or not isinstance(uri, str):
        return None
    if '#' in uri:
        fragment = uri.split('#')[-1]
        if fragment.endswith('Member'):
            fragment = fragment[:-6]
        return fragment
    return uri


# NOTE: extract_investment_id and is_individual_investment functions removed.
# Investment identification is now handled by get_investment_identifier() which
# accesses xbrl.contexts directly instead of relying on dimensions in dataframe.


def classify_investment_type(investment_type: str, has_principal: bool, has_shares: bool) -> str:
    """
    Classify investment as 'Debt', 'Equity', or 'Unknown'.
    
    Uses multiple signals:
    1. Investment type string keywords
    2. Presence of principal (debt) vs shares (equity)
    """
    if investment_type:
        type_lower = investment_type.lower()
        
        # Check for debt keywords
        for keyword in DEBT_TYPE_KEYWORDS:
            if keyword in type_lower:
                return 'Debt'
        
        # Check for equity keywords
        for keyword in EQUITY_TYPE_KEYWORDS:
            if keyword in type_lower:
                return 'Equity'
    
    # Fall back to field presence
    if has_principal and not has_shares:
        return 'Debt'
    if has_shares and not has_principal:
        return 'Equity'
    
    # If both or neither, try to infer
    if has_principal:
        return 'Debt'  # Principal is stronger signal
    if has_shares:
        return 'Equity'
    
    return 'Unknown'


def get_affiliation_category(affiliation: str, dimensions: dict) -> str:
    """Determine affiliation category from enumeration or dimensions."""
    if affiliation:
        aff_lower = affiliation.lower()
        if 'controlled' in aff_lower and 'noncontrolled' not in aff_lower:
            return 'Controlled Affiliate'
        if 'noncontrolled' in aff_lower or 'non-controlled' in aff_lower:
            return 'Non-Controlled Affiliate'
        if 'affiliated' in aff_lower:
            return 'Affiliate'
        if 'unaffiliated' in aff_lower:
            return 'Unaffiliated'
    
    # Check dimensions
    if dimensions:
        dims_str = str(dimensions)
        if 'ControlledMember' in dims_str and 'Noncontrolled' not in dims_str:
            return 'Controlled Affiliate'
        if 'NoncontrolledMember' in dims_str:
            return 'Non-Controlled Affiliate'
        if 'AffiliatedIssuerMember' in dims_str:
            return 'Affiliate'
        if 'UnaffiliatedIssuerMember' in dims_str:
            return 'Unaffiliated'
    
    return 'Unaffiliated'  # Default assumption


# ============================================================================
# MAIN EXTRACTION LOGIC
# ============================================================================

def get_investment_identifier(xbrl, context_ref: str) -> Optional[str]:
    """
    Extract investment identifier from context dimensions.

    Based on ARCC investigation findings: Investment identifiers are in the
    context dimensions with key 'us-gaap:InvestmentIdentifierAxis'.

    Args:
        xbrl: XBRL object with contexts dictionary
        context_ref: Context reference ID from a fact

    Returns:
        Investment identifier string or None
    """
    contexts = xbrl.contexts
    if context_ref not in contexts:
        return None

    context = contexts[context_ref]
    if not hasattr(context, 'dimensions'):
        return None

    dims = context.dimensions
    if not dims:
        return None

    # Primary method: InvestmentIdentifierAxis
    inv_id = dims.get('us-gaap:InvestmentIdentifierAxis')
    if inv_id:
        return inv_id

    # Fallback: Check for other identifier dimensions
    for key, value in dims.items():
        if 'Identifier' in key or 'Investment' in key:
            return value

    return None


def extract_raw_facts(xbrl) -> pd.DataFrame:
    """
    Extract all investment-related facts from XBRL across all statements.

    Based on ARCC investigation: Investment data is spread across multiple statements:
    - CONSOLIDATEDSCHEDULEOFINVESTMENTS: Interest rates, spreads, principal, shares
    - CONSOLIDATEDBALANCESHEET: Fair values
    - CONSOLIDATEDBALANCESHEETParenthetical: Cost basis

    This function queries all facts and filters to those with investment identifiers.
    Concept names are normalized (namespace prefixes stripped) for robust matching.
    """
    # Get all facts as dataframe
    all_facts = xbrl.facts.query().to_dataframe()

    if all_facts.empty:
        return pd.DataFrame()

    # Add investment identifiers from context dimensions
    all_facts['investment_id'] = all_facts['context_ref'].apply(
        lambda ctx: get_investment_identifier(xbrl, ctx)
    )

    # Filter to facts with investment identifiers
    investment_facts = all_facts[all_facts['investment_id'].notna()].copy()

    if investment_facts.empty:
        return pd.DataFrame()

    # Normalize concept names (strip namespace prefixes) for matching
    investment_facts['normalized_concept'] = investment_facts['concept'].apply(normalize_concept)

    # Build normalized concept-to-field mapping
    concept_to_field = {}
    for field_name, concept in {**COMMON_CONCEPTS, **DEBT_CONCEPTS, **EQUITY_CONCEPTS}.items():
        # Concepts in our dictionaries are already without namespace prefixes
        normalized = normalize_concept(concept)
        concept_to_field[normalized] = field_name

    # Map field names using normalized concepts
    investment_facts['field'] = investment_facts['normalized_concept'].map(concept_to_field)

    # Filter to recognized concepts
    investment_facts = investment_facts[investment_facts['field'].notna()]

    return investment_facts


def pivot_to_investments(facts_df: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot facts to one row per investment.

    Handles multiple facts per investment by taking the first value for each field.
    Some investments may have multiple facts for the same concept (e.g., multiple
    tranches or reporting periods) - we take the most recent/first value.
    """
    if facts_df.empty:
        return pd.DataFrame()

    # Group by investment_id and field, take first value
    investments = defaultdict(dict)

    for _, row in facts_df.iterrows():
        inv_id = row['investment_id']
        if not inv_id:
            continue

        field = row['field']

        # Skip if we already have this field for this investment
        if field in investments[inv_id]:
            continue

        # Get value - prefer numeric_value if available
        value = row.get('numeric_value')
        if pd.isna(value):
            value = row.get('value')

        # Parse extensible enumerations (URIs)
        if field in ['issuer_name', 'investment_type', 'industry', 'affiliation', 'rate_type']:
            value = parse_enum_uri(str(value)) if pd.notna(value) else None

        investments[inv_id][field] = value

        # Store period for reference (if not already stored)
        if 'period_end' not in investments[inv_id]:
            period_end = row.get('period_instant') or row.get('period_end')
            if pd.notna(period_end):
                investments[inv_id]['period_end'] = period_end

    # Convert to DataFrame
    df = pd.DataFrame.from_dict(investments, orient='index')
    df.index.name = 'investment_id'
    df = df.reset_index()

    return df


def split_debt_equity(investments_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split investments into debt and equity DataFrames.

    Classification logic:
    1. Check investment_type for keywords
    2. Check for presence of principal (debt) vs shares (equity)
    3. Default to Unknown if ambiguous
    """
    if investments_df.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Classify each investment
    def classify_row(row):
        inv_type = row.get('investment_type', '')
        has_principal = pd.notna(row.get('principal'))
        has_shares = pd.notna(row.get('shares'))
        return classify_investment_type(inv_type, has_principal, has_shares)

    investments_df = investments_df.copy()
    investments_df['asset_class'] = investments_df.apply(classify_row, axis=1)

    # Add affiliation category from affiliation field
    investments_df['affiliation_category'] = investments_df.apply(
        lambda row: get_affiliation_category(row.get('affiliation'), None),
        axis=1
    )

    # Split
    debt_df = investments_df[investments_df['asset_class'] == 'Debt'].copy()
    equity_df = investments_df[investments_df['asset_class'] == 'Equity'].copy()
    unknown_df = investments_df[investments_df['asset_class'] == 'Unknown'].copy()

    # Report unknowns
    if len(unknown_df) > 0:
        print(f"\nWARNING: {len(unknown_df)} investments could not be classified as debt or equity")
        print("Sample unknown investments:")
        for idx, row in unknown_df.head(5).iterrows():
            inv_id = row['investment_id']
            inv_type = row.get('investment_type', 'N/A')
            has_prin = 'Principal' if pd.notna(row.get('principal')) else ''
            has_shares = 'Shares' if pd.notna(row.get('shares')) else ''
            print(f"  - {inv_id[:60]}... ({inv_type}, {has_prin} {has_shares})")

    # Select appropriate columns for each
    debt_columns = [
        'investment_id', 'issuer_name', 'investment_type', 'industry',
        'affiliation_category', 'fair_value', 'cost', 'principal',
        'interest_rate', 'rate_type', 'spread', 'floor', 'pik_rate', 'cash_rate',
        'maturity_date', 'acquisition_date', 'pct_net_assets',
        'is_restricted', 'is_level3', 'is_non_income', 'period_end'
    ]

    equity_columns = [
        'investment_id', 'issuer_name', 'investment_type', 'industry',
        'affiliation_category', 'fair_value', 'cost', 'shares',
        'acquisition_date', 'pct_net_assets',
        'is_restricted', 'is_level3', 'is_non_income', 'period_end'
    ]

    # Filter to existing columns
    debt_columns = [c for c in debt_columns if c in debt_df.columns]
    equity_columns = [c for c in equity_columns if c in equity_df.columns]

    debt_df = debt_df[debt_columns] if debt_columns else debt_df
    equity_df = equity_df[equity_columns] if equity_columns else equity_df

    return debt_df, equity_df


def extract_affiliated_rollforward(xbrl) -> pd.DataFrame:
    """
    Extract affiliated investment roll-forward data.

    Looks for facts with affiliation dimensions indicating affiliated issuers.
    Uses normalized concept names for robust matching.
    """
    # Get all facts
    all_facts_df = xbrl.facts.query().to_dataframe()

    if all_facts_df.empty:
        return pd.DataFrame()

    # Normalize concept names
    all_facts_df['normalized_concept'] = all_facts_df['concept'].apply(normalize_concept)

    contexts = xbrl.contexts
    all_facts = []

    # Get fair values with affiliation dimension
    fv_concept_normalized = normalize_concept(COMMON_CONCEPTS['fair_value'])
    fv_facts = all_facts_df[all_facts_df['normalized_concept'] == fv_concept_normalized].copy()
    if not fv_facts.empty:
        # Check contexts for affiliation dimension
        def is_affiliated(context_ref):
            if context_ref not in contexts:
                return False
            ctx = contexts[context_ref]
            if not hasattr(ctx, 'dimensions'):
                return False
            dims = ctx.dimensions
            return any('Affiliated' in str(k) or 'Affiliated' in str(v)
                      for k, v in dims.items()) if dims else False

        fv_facts['is_affiliated'] = fv_facts['context_ref'].apply(is_affiliated)
        affiliated_fv = fv_facts[fv_facts['is_affiliated']].copy()

        if not affiliated_fv.empty:
            affiliated_fv['field'] = 'fair_value'
            all_facts.append(affiliated_fv)

    # Get roll-forward activity using normalized concepts
    for field_name, concept in AFFILIATED_CONCEPTS.items():
        concept_normalized = normalize_concept(concept)
        df = all_facts_df[all_facts_df['normalized_concept'] == concept_normalized].copy()
        if not df.empty:
            df['field'] = field_name
            all_facts.append(df)
    
    if not all_facts:
        return pd.DataFrame()

    combined = pd.concat(all_facts, ignore_index=True)

    # Add investment identifiers
    combined['investment_id'] = combined['context_ref'].apply(
        lambda ctx: get_investment_identifier(xbrl, ctx)
    )

    # Filter to individual investments
    individual = combined[combined['investment_id'].notna()].copy()

    if individual.empty:
        # Return aggregate data if no individual positions found
        available_cols = [c for c in ['field', 'value', 'period_start', 'period_end']
                         if c in combined.columns]
        return combined[available_cols].drop_duplicates() if available_cols else combined

    # Pivot by investment
    rollforward = defaultdict(dict)
    for _, row in individual.iterrows():
        inv_id = row['investment_id']
        if inv_id:
            field = row['field']
            value = row.get('numeric_value') if pd.notna(row.get('numeric_value')) else row.get('value')
            rollforward[inv_id][field] = value
            rollforward[inv_id]['period_start'] = row.get('period_start')
            rollforward[inv_id]['period_end'] = row.get('period_end') or row.get('period_instant')

    df = pd.DataFrame.from_dict(rollforward, orient='index')
    df.index.name = 'investment_id'
    return df.reset_index()


def extract_portfolio_summary(xbrl, debt_df: pd.DataFrame, equity_df: pd.DataFrame) -> pd.DataFrame:
    """Generate portfolio summary statistics."""
    summary = []
    
    # Totals from extracted data
    if not debt_df.empty and 'fair_value' in debt_df.columns:
        debt_fv = debt_df['fair_value'].sum()
        debt_cost = debt_df['cost'].sum() if 'cost' in debt_df.columns else None
        summary.append({
            'category': 'Asset Class',
            'subcategory': 'Debt Investments',
            'fair_value': debt_fv,
            'cost': debt_cost,
            'count': len(debt_df)
        })
    
    if not equity_df.empty and 'fair_value' in equity_df.columns:
        equity_fv = equity_df['fair_value'].sum()
        equity_cost = equity_df['cost'].sum() if 'cost' in equity_df.columns else None
        summary.append({
            'category': 'Asset Class',
            'subcategory': 'Equity Investments',
            'fair_value': equity_fv,
            'cost': equity_cost,
            'count': len(equity_df)
        })
    
    # Industry breakdown
    for df, asset_class in [(debt_df, 'Debt'), (equity_df, 'Equity')]:
        if not df.empty and 'industry' in df.columns and 'fair_value' in df.columns:
            industry_totals = df.groupby('industry')['fair_value'].sum()
            for industry, fv in industry_totals.items():
                if industry and pd.notna(industry):
                    summary.append({
                        'category': f'Industry ({asset_class})',
                        'subcategory': industry,
                        'fair_value': fv,
                        'count': len(df[df['industry'] == industry])
                    })
    
    # Affiliation breakdown
    all_investments = pd.concat([debt_df, equity_df], ignore_index=True) if not debt_df.empty or not equity_df.empty else pd.DataFrame()
    if not all_investments.empty and 'affiliation_category' in all_investments.columns:
        aff_totals = all_investments.groupby('affiliation_category')['fair_value'].sum()
        for aff, fv in aff_totals.items():
            summary.append({
                'category': 'Affiliation',
                'subcategory': aff,
                'fair_value': fv,
                'count': len(all_investments[all_investments['affiliation_category'] == aff])
            })
    
    # Grand totals
    total_fv = (debt_df['fair_value'].sum() if not debt_df.empty and 'fair_value' in debt_df.columns else 0) + \
               (equity_df['fair_value'].sum() if not equity_df.empty and 'fair_value' in equity_df.columns else 0)
    total_cost = (debt_df['cost'].sum() if not debt_df.empty and 'cost' in debt_df.columns else 0) + \
                 (equity_df['cost'].sum() if not equity_df.empty and 'cost' in equity_df.columns else 0)
    
    summary.append({
        'category': 'Total',
        'subcategory': 'All Investments',
        'fair_value': total_fv,
        'cost': total_cost,
        'unrealized_gain_loss': total_fv - total_cost if total_cost else None,
        'count': len(debt_df) + len(equity_df)
    })
    
    # Unique issuers
    all_issuers = set()
    if not debt_df.empty and 'issuer_name' in debt_df.columns:
        all_issuers.update(debt_df['issuer_name'].dropna().unique())
    if not equity_df.empty and 'issuer_name' in equity_df.columns:
        all_issuers.update(equity_df['issuer_name'].dropna().unique())
    
    summary.append({
        'category': 'Metrics',
        'subcategory': 'Unique Portfolio Companies',
        'count': len(all_issuers)
    })
    
    return pd.DataFrame(summary)


def extract_all_investments(xbrl) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Main extraction function.
    
    Returns:
        debt_df: Debt investments with rate/maturity data
        equity_df: Equity investments with shares data
        affiliated_df: Affiliated investment roll-forward
        summary_df: Portfolio summary statistics
    """
    print("Extracting raw XBRL facts...")
    raw_facts = extract_raw_facts(xbrl)
    
    if raw_facts.empty:
        print("WARNING: No Schedule of Investments facts found")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    print(f"Found {len(raw_facts)} total facts")
    
    print("Pivoting to investment-level data...")
    investments = pivot_to_investments(raw_facts)
    
    if investments.empty:
        print("WARNING: Could not extract individual investments")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    print(f"Found {len(investments)} individual investments")
    
    print("Classifying debt vs equity...")
    debt_df, equity_df = split_debt_equity(investments)
    print(f"  Debt investments: {len(debt_df)}")
    print(f"  Equity investments: {len(equity_df)}")
    
    print("Extracting affiliated roll-forward...")
    affiliated_df = extract_affiliated_rollforward(xbrl)
    print(f"  Affiliated records: {len(affiliated_df)}")
    
    print("Generating portfolio summary...")
    summary_df = extract_portfolio_summary(xbrl, debt_df, equity_df)
    
    return debt_df, equity_df, affiliated_df, summary_df


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

def get_bdc_filing(ticker: str, form: str = "10-K", year: Optional[int] = None):
    """Get BDC filing by ticker."""
    company = Company(ticker)

    if year:
        filings = company.get_filings(form=form, year=year, amendments=False)
    else:
        filings = company.get_filings(form=form, amendments=False)

    if not filings or len(filings) == 0:
        raise ValueError(f"No {form} filings found for {ticker}")

    return filings.latest()


def main():
    """Main entry point for CLI usage."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    ticker = sys.argv[1].upper()
    form = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] in ['10-K', '10-Q'] else "10-K"
    year = None
    identity = "BDC Research research@example.com"

    # Parse arguments
    for i, arg in enumerate(sys.argv[2:], start=2):
        if arg.isdigit() and len(arg) == 4:
            year = int(arg)
        elif arg == '--identity' and i + 1 < len(sys.argv):
            identity = sys.argv[i + 1]

    # Set identity (required by SEC)
    set_identity(identity)
    
    print(f"\n{'='*70}")
    print(f"BDC Schedule of Investments Extractor")
    print(f"{'='*70}")
    print(f"Ticker: {ticker}")
    print(f"Form: {form}" + (f", Year: {year}" if year else " (latest)"))
    print(f"{'='*70}\n")
    
    # Get filing
    try:
        filing = get_bdc_filing(ticker, form, year)
        print(f"Filing: {filing.form} filed {filing.filing_date}")
        print(f"Accession: {filing.accession_number}\n")
    except Exception as e:
        print(f"ERROR: Could not get filing: {e}")
        sys.exit(1)
    
    # Parse XBRL
    try:
        xbrl = filing.xbrl()
        print(f"XBRL parsed successfully")
        entity_info = xbrl.entity_info or {}
        print(f"Entity: {entity_info.get('entity_name', 'Unknown')}")
        print(f"Fiscal Period: {entity_info.get('document_fiscal_period_focus', 'Unknown')}")
        print(f"Fiscal Year: {entity_info.get('document_fiscal_year_focus', 'Unknown')}\n")
    except Exception as e:
        print(f"ERROR: Could not parse XBRL: {e}")
        print("This filing may not have XBRL data (pre-2022) or uses non-standard format")
        sys.exit(1)
    
    # Extract
    debt_df, equity_df, affiliated_df, summary_df = extract_all_investments(xbrl)
    
    # Save outputs
    print(f"\n{'='*70}")
    print("SAVING OUTPUTS")
    print(f"{'='*70}\n")
    
    base_name = f"{ticker}_{form.replace('-', '')}"
    
    if not debt_df.empty:
        debt_file = f"{base_name}_debt_investments.csv"
        debt_df.to_csv(debt_file, index=False)
        print(f"✓ Debt investments: {debt_file} ({len(debt_df)} rows)")
        
        # Show sample
        if 'fair_value' in debt_df.columns:
            total_debt_fv = debt_df['fair_value'].sum()
            print(f"  Total Debt Fair Value: ${total_debt_fv:,.0f}")
    
    if not equity_df.empty:
        equity_file = f"{base_name}_equity_investments.csv"
        equity_df.to_csv(equity_file, index=False)
        print(f"✓ Equity investments: {equity_file} ({len(equity_df)} rows)")
        
        if 'fair_value' in equity_df.columns:
            total_equity_fv = equity_df['fair_value'].sum()
            print(f"  Total Equity Fair Value: ${total_equity_fv:,.0f}")
    
    if not affiliated_df.empty:
        aff_file = f"{base_name}_affiliated_rollforward.csv"
        affiliated_df.to_csv(aff_file, index=False)
        print(f"✓ Affiliated roll-forward: {aff_file} ({len(affiliated_df)} rows)")
    
    if not summary_df.empty:
        summary_file = f"{base_name}_portfolio_summary.csv"
        summary_df.to_csv(summary_file, index=False)
        print(f"✓ Portfolio summary: {summary_file}")
        
        # Print summary
        print(f"\n{'='*70}")
        print("PORTFOLIO SUMMARY")
        print(f"{'='*70}")
        for _, row in summary_df.iterrows():
            if row['category'] == 'Total':
                print(f"\n{row['subcategory']}:")
                print(f"  Fair Value: ${row['fair_value']:,.0f}")
                if pd.notna(row.get('cost')):
                    print(f"  Cost: ${row['cost']:,.0f}")
                if pd.notna(row.get('unrealized_gain_loss')):
                    print(f"  Unrealized Gain/Loss: ${row['unrealized_gain_loss']:,.0f}")
                print(f"  Position Count: {row['count']}")
    
    print(f"\n{'='*70}")
    print("Extraction complete!")
    print(f"{'='*70}\n")
    
    return debt_df, equity_df, affiliated_df, summary_df


if __name__ == "__main__":
    main()
