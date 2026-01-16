"""
Spike test: Evaluate edgartools for Schedule of Investments extraction
Run: python -m src.spike_edgartools
"""

from edgar import set_identity, Company
import pandas as pd

# Required: Set identity for SEC
set_identity("BDC Analysis Project stephen.parton@example.com")

# Test with ARCC (Ares Capital) - largest BDC, CIK 1287750
print("=" * 60)
print("SPIKE TEST: EdgarTools for Schedule of Investments")
print("=" * 60)

# Step 1: Get company and latest 10-K
print("\n1. Getting ARCC (Ares Capital) latest 10-K...")
company = Company("ARCC")
print(f"Company: {company.name}")
print(f"CIK: {company.cik}")

filings = company.get_filings(form="10-K")
latest_10k = filings[0]
print(f"\nLatest 10-K: {latest_10k.accession_number}")
print(f"Filing date: {latest_10k.filing_date}")

# Step 2: Search for Schedule of Investments in the filing
print("\n2. Searching for 'Schedule of Investments' in filing...")
results = latest_10k.search("Schedule of Investments")
print(f"Found {len(results)} matches")

if results:
    print("\nTop 3 matches:")
    count = 0
    for i, match in enumerate(results):
        if count >= 3:
            break
        print(f"\n--- Match {i+1} (score: {match.score:.2f}) ---")
        print(str(match)[:500] + "...")
        count += 1

# Step 3: Try to access XBRL data
print("\n3. Checking XBRL data availability...")
try:
    xbrl = latest_10k.xbrl()
    print(f"XBRL available: Yes")

    # List available statements
    print("\nAvailable statements:")
    if hasattr(xbrl, 'statements'):
        stmt_attrs = [attr for attr in dir(xbrl.statements) if not attr.startswith('_')]
        for stmt_name in stmt_attrs[:10]:  # Show first 10
            print(f"  - {stmt_name}")
        if len(stmt_attrs) > 10:
            print(f"  ... and {len(stmt_attrs) - 10} more")
except Exception as e:
    print(f"XBRL error: {e}")

# Step 4: Get raw HTML and look for tables
print("\n4. Examining HTML structure...")
try:
    html_content = latest_10k.html()

    # Count tables
    table_count = html_content.lower().count('<table')
    print(f"Total tables in filing: {table_count}")

    # Look for Schedule of Investments table
    soi_pos = html_content.lower().find('schedule of investments')
    if soi_pos > 0:
        print(f"'Schedule of Investments' found at position: {soi_pos}")

        # Find nearest table after this position
        next_table = html_content.lower().find('<table', soi_pos)
        if next_table > 0:
            print(f"Next table starts at position: {next_table}")

            # Extract a snippet of the table
            table_end = html_content.lower().find('</table>', next_table)
            if table_end > 0:
                table_html = html_content[next_table:table_end+8]
                print(f"Table size: {len(table_html)} characters")

                # Save sample for inspection
                with open('outputs/sample_soi_table.html', 'w') as f:
                    f.write(table_html)
                print("Saved sample table to outputs/sample_soi_table.html")
except Exception as e:
    print(f"HTML error: {e}")

# Step 5: Check all 10 target BDCs for 10-K availability
print("\n5. Checking 10-K availability for all target BDCs...")
TOP_10_BDCS = {
    1287750: "ARCC",
    1631115: "FSK",
    1838831: "BXSL",
    1758190: "ORCC",
    1476765: "GBDC",
    1287032: "PSEC",
    1396440: "MAIN",
    1280784: "HTGC",
    1496099: "NMFC",
    1414932: "OCSL",
}

filing_info = []
for cik, ticker in TOP_10_BDCS.items():
    try:
        comp = Company(cik)
        f = comp.get_filings(form="10-K")[0]
        filing_info.append({
            'ticker': ticker,
            'cik': cik,
            'name': comp.name,
            'accession': f.accession_number,
            'filing_date': str(f.filing_date),
            'adsh': f.accession_number.replace('-', '')  # Format for SEC Data Sets
        })
        print(f"  ✓ {ticker}: {f.filing_date} ({f.accession_number})")
    except Exception as e:
        print(f"  ✗ {ticker}: Error - {e}")

# Save filing info for reference
if filing_info:
    df = pd.DataFrame(filing_info)
    df.to_csv('outputs/target_bdc_filings.csv', index=False)
    print(f"\nSaved {len(filing_info)} filing references to outputs/target_bdc_filings.csv")

# Summary
print("\n" + "=" * 60)
print("SPIKE TEST SUMMARY")
print("=" * 60)
print("""
Questions to answer:
1. Does filing.search() find the Schedule of Investments section?
2. Is XBRL data useful for SOI (or just standard financials)?
3. Can we parse the HTML tables reasonably?
4. Do all 10 BDCs have accessible 10-K filings?

Next steps based on findings:
- If HTML tables are clean → consider direct EDGAR parsing
- If messy → stick with SEC BDC Data Sets approach
- Check outputs/sample_soi_table.html to see actual table structure
""")
