"""
Investigate FSK and ORCC accessibility issues
Run: python -m src.investigate_missing_bdcs
"""
from edgar import set_identity, Company

set_identity("BDC Analysis Project stephen.parton@example.com")

# Try different approaches for FSK (CIK 1631115)
print("=" * 60)
print("=== Investigating FSK (FS KKR Capital Corp) ===")
print("=" * 60)
try:
    # Try by CIK
    company = Company(1631115)
    print(f"Company name: {company.name}")
    print(f"CIK: {company.cik}")

    # Get all filings
    filings = company.get_filings()
    print(f"Total filings available: {len(filings)}")

    # Check what form types are available
    form_types = {}
    for f in filings[:100]:  # Check first 100
        form = f.form
        if form not in form_types:
            form_types[form] = []
        form_types[form].append(f.filing_date)

    print(f"\nForm types found (first 100 filings):")
    for form, dates in sorted(form_types.items()):
        print(f"  {form}: {len(dates)} filings, latest: {dates[0]}")

    # Try specific forms
    print("\nTrying specific forms:")
    for form in ["10-K", "10-K/A", "10-Q", "N-CSR", "N-2", "N-2/A"]:
        try:
            form_filings = company.get_filings(form=form)
            if len(form_filings) > 0:
                print(f"  ✓ {form}: {len(form_filings)} filings, latest: {form_filings[0].filing_date}")
            else:
                print(f"  ✗ {form}: No filings found")
        except Exception as e:
            print(f"  ✗ {form}: Error - {e}")

except Exception as e:
    print(f"Error accessing FSK: {e}")

print("\n" + "=" * 60)
print("=== Investigating ORCC (Blue Owl Capital Corporation) ===")
print("=" * 60)
try:
    company = Company(1758190)
    print(f"Company name: {company.name}")
    print(f"CIK: {company.cik}")

    filings = company.get_filings()
    print(f"Total filings available: {len(filings)}")

    # Check form types
    form_types = {}
    for f in filings[:100]:
        form = f.form
        if form not in form_types:
            form_types[form] = []
        form_types[form].append(f.filing_date)

    print(f"\nForm types found (first 100 filings):")
    for form, dates in sorted(form_types.items()):
        print(f"  {form}: {len(dates)} filings, latest: {dates[0]}")

    # Try specific forms
    print("\nTrying specific forms:")
    for form in ["10-K", "10-K/A", "10-Q", "N-CSR", "N-2", "N-2/A"]:
        try:
            form_filings = company.get_filings(form=form)
            if len(form_filings) > 0:
                print(f"  ✓ {form}: {len(form_filings)} filings, latest: {form_filings[0].filing_date}")
            else:
                print(f"  ✗ {form}: No filings found")
        except Exception as e:
            print(f"  ✗ {form}: Error - {e}")

except Exception as e:
    print(f"Error accessing ORCC: {e}")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("""
BDCs may file as:
- 10-K: Regular business (operating company structure)
- N-CSR: Registered Investment Company (RIC structure)
- N-2: RIC registration statement

If FSK/ORCC use RIC structure, look for N-CSR filings instead of 10-K.
N-CSR filings also contain Schedule of Investments.
""")
