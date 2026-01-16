"""
Test parser on all 10 target BDCs and combine results.
Run: python -m src.test_all_bdcs
"""

import pandas as pd
from edgar import set_identity
from src.edgar_parser import get_bdc_10k, parse_schedule_of_investments, TOP_10_BDCS

set_identity("BDC Analysis Project stephen.parton@example.com")

print("=" * 60)
print("BDC PORTFOLIO HOLDINGS EXTRACTION")
print("=" * 60)
print()

all_holdings = []
success_count = 0
fail_count = 0

for cik, info in TOP_10_BDCS.items():
    ticker = info['ticker']
    name = info['name']

    print(f"\n{'='*60}")
    print(f"{ticker} - {name}")
    print(f"{'='*60}")

    try:
        # Get latest 10-K
        filing = get_bdc_10k(ticker)
        print(f"Filing: {filing.accession_number} ({filing.filing_date})")

        # Parse holdings
        holdings = parse_schedule_of_investments(filing, bdc_name=name)

        if len(holdings) > 0:
            all_holdings.append(holdings)
            success_count += 1

            # Show summary
            total_fv = holdings['fair_value'].sum()
            print(f"\n✓ SUCCESS: Extracted {len(holdings)} holdings")
            print(f"  Total Fair Value: ${total_fv/1_000_000_000:.2f}B")

            # Show sample
            print(f"\n  Sample holdings:")
            for _, row in holdings.head(3).iterrows():
                print(f"    - {row['company_name']}: ${row['fair_value']/1_000_000:.1f}M")
        else:
            print(f"\n✗ FAILED: No holdings extracted")
            fail_count += 1

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        fail_count += 1

# Combine all holdings
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

if all_holdings:
    combined_df = pd.concat(all_holdings, ignore_index=True)

    print(f"\n✓ Successfully parsed {success_count}/10 BDCs")
    print(f"✗ Failed: {fail_count}/10 BDCs")
    print(f"\nTotal holdings extracted: {len(combined_df):,}")

    # BDC breakdown
    print(f"\nHoldings by BDC:")
    bdc_summary = combined_df.groupby('bdc_name').agg({
        'company_name': 'count',
        'fair_value': 'sum'
    }).rename(columns={'company_name': 'holdings_count'})
    bdc_summary['fair_value_billions'] = bdc_summary['fair_value'] / 1_000_000_000
    bdc_summary = bdc_summary.sort_values('fair_value', ascending=False)

    for bdc_name, row in bdc_summary.iterrows():
        print(f"  {bdc_name}:")
        print(f"    {row['holdings_count']:,} holdings, ${row['fair_value_billions']:.2f}B fair value")

    # Save combined results
    output_path = 'outputs/all_bdc_holdings.csv'
    combined_df.to_csv(output_path, index=False)
    print(f"\n✓ Saved all holdings to {output_path}")

else:
    print("\n✗ No holdings extracted from any BDC")
