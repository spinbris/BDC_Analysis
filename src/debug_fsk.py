"""
Debug FSK (FS KKR Capital Corp) table structure
Run: python -m src.debug_fsk
"""

import pandas as pd
from edgar import set_identity
from src.edgar_parser import get_bdc_10k
from io import StringIO

set_identity("BDC Analysis Project stephen.parton@example.com")

print("=" * 60)
print("DEBUGGING FSK (FS KKR Capital Corp)")
print("=" * 60)

# Get filing
filing = get_bdc_10k("FSK")
print(f"Filing: {filing.accession_number} ({filing.filing_date})")

html_content = filing.html()

# Find SOI position
soi_pos = html_content.lower().find('schedule of investments')
print(f"\n'Schedule of Investments' found at position {soi_pos:,}")

# Find first few large tables after SOI
search_pos = soi_pos
table_count = 0

while table_count < 3:
    next_table = html_content.lower().find('<table', search_pos)
    if next_table == -1:
        break

    table_end = html_content.lower().find('</table>', next_table)
    if table_end == -1:
        break

    table_html = html_content[next_table:table_end+8]
    table_size = len(table_html)

    # Check if it looks like SOI table
    llc_count = table_html.count('LLC') + table_html.count('Inc.') + table_html.count('Corp.')
    has_fair_value = 'fair value' in table_html.lower()
    has_principal = 'principal' in table_html.lower()

    if table_size > 50000 and llc_count > 5:
        print(f"\n{'='*60}")
        print(f"TABLE {table_count + 1}")
        print(f"{'='*60}")
        print(f"Size: {table_size/1024:.1f}KB")
        print(f"Company mentions: {llc_count}")
        print(f"Has 'fair value': {has_fair_value}")
        print(f"Has 'principal': {has_principal}")

        # Try to parse with pandas
        try:
            df = pd.read_html(StringIO(table_html))[0]
            print(f"DataFrame shape: {df.shape}")

            # Show first 8 rows
            print(f"\nFirst 8 rows:")
            print(df.head(8).to_string())

            # Check each row for header indicators
            print(f"\nChecking rows 0-6 for headers:")
            for i in range(min(7, len(df))):
                row_text = ' '.join([str(v).lower() for v in df.iloc[i].values if pd.notna(v)])
                has_company = 'company' in row_text
                has_fv = 'fair value' in row_text
                print(f"  Row {i}: company={has_company}, fair_value={has_fv}")
                if has_company or has_fv:
                    print(f"    Text: {row_text[:300]}")

            # Save first table for detailed inspection
            if table_count == 0:
                output_path = 'outputs/fsk_first_table.html'
                with open(output_path, 'w') as f:
                    f.write(table_html)
                print(f"\n✓ Saved first table to {output_path}")

                df.to_csv('outputs/fsk_first_table.csv', index=False)
                print(f"✓ Saved DataFrame to outputs/fsk_first_table.csv")

        except Exception as e:
            print(f"Error parsing table: {e}")

        table_count += 1

    search_pos = table_end + 8

    if search_pos > soi_pos + 5000000:
        break

print(f"\n{'='*60}")
print(f"Found {table_count} candidate SOI tables")
print(f"{'='*60}")
