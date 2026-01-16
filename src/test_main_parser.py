"""
Test updated parser on MAIN
Run: python -m src.test_main_parser
"""

from edgar import set_identity
from src.edgar_parser import get_bdc_10k, parse_schedule_of_investments

set_identity("BDC Analysis Project stephen.parton@example.com")

print("=" * 60)
print("Testing parser on MAIN (Main Street Capital)")
print("=" * 60)

filing = get_bdc_10k("MAIN")
print(f"Filing: {filing.accession_number} ({filing.filing_date})")

holdings = parse_schedule_of_investments(filing, bdc_name="Main Street Capital Corporation")

if len(holdings) > 0:
    total_fv = holdings['fair_value'].sum()
    print(f"\n✓ SUCCESS: Extracted {len(holdings)} holdings")
    print(f"  Total Fair Value: ${total_fv/1_000_000_000:.2f}B")

    # Show sample
    print(f"\n  Sample holdings:")
    for _, row in holdings.head(10).iterrows():
        print(f"    - {row['company_name']}: {row['investment_type']} - ${row['fair_value']/1_000_000:.1f}M")

    # Save
    holdings.to_csv('outputs/main_holdings_test.csv', index=False)
    print(f"\n✓ Saved to outputs/main_holdings_test.csv")
else:
    print("\n✗ FAILED: No holdings extracted")
