"""Download BDC Data Sets from SEC"""

import zipfile
from pathlib import Path
from typing import Optional

import requests


def download_bdc_dataset(
    output_dir: Path,
    period: str = "latest",
    user_agent: str = "BDC Analysis Project stephen.parton@example.com"
) -> Path:
    """Download and extract BDC Data Set from SEC

    Args:
        output_dir: Directory to extract data to (e.g., data/raw/)
        period: "latest" for most recent (2025_11), or historical like "2024q4", "2024q3"
        user_agent: User-Agent header for SEC compliance

    Returns:
        Path to extracted directory containing .tsv files

    Examples:
        download_bdc_dataset(Path("data/raw"))  # Downloads 2025_11_bdc.zip
        download_bdc_dataset(Path("data/raw"), "2024q4")  # Downloads 2024q4_bdc.zip
        download_bdc_dataset(Path("data/raw"), "2025_11")  # Downloads 2025_11_bdc.zip

    Note:
        SEC requires a User-Agent header identifying the requester.
        URL pattern: https://www.sec.gov/files/structureddata/data/business-development-company-bdc-data-sets/YYYY_MM_bdc.zip
        Monthly files (YYYY_MM) are large (~26MB) with annual 10-K data.
        Quarterly files (YYYYqN) are smaller (~17MB) with 10-Q updates.
    """
    # Determine filename based on period
    if period == "latest":
        filename = "2025_11_bdc.zip"  # Most recent as of Jan 2026
    else:
        filename = f"{period}_bdc.zip"

    base_url = "https://www.sec.gov/files/structureddata/data/business-development-company-bdc-data-sets"
    url = f"{base_url}/{filename}"

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    zip_path = output_dir / filename

    print(f"Downloading BDC Data Set from SEC...")
    print(f"  Period: {period}")
    print(f"  URL: {url}")

    headers = {
        'User-Agent': user_agent,
        'Accept-Encoding': 'gzip, deflate',
    }

    response = requests.get(url, headers=headers, stream=True)
    response.raise_for_status()

    # Download with progress indication
    total_size = int(response.headers.get('content-length', 0))
    block_size = 8192
    downloaded = 0

    with open(zip_path, 'wb') as f:
        for chunk in response.iter_content(block_size):
            f.write(chunk)
            downloaded += len(chunk)
            if total_size > 0:
                pct = (downloaded / total_size) * 100
                print(f"  Downloaded: {downloaded:,} / {total_size:,} bytes ({pct:.1f}%)", end='\r')

    print(f"\n✓ Download complete: {zip_path}")

    # Extract ZIP directly to output_dir (not nested subdirectory)
    print(f"Extracting to {output_dir}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Create subdirectory for this period
        extracted_dir = output_dir / f"bdc_{period}" if period != "latest" else output_dir / "bdc-data-sets"
        extracted_dir.mkdir(exist_ok=True)
        zip_ref.extractall(extracted_dir)

    # List extracted files
    tsv_files = sorted(extracted_dir.glob("*.tsv"))
    print(f"✓ Extracted {len(tsv_files)} TSV files:")
    for f in tsv_files:
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"  - {f.name} ({size_mb:.1f} MB)")

    # Clean up ZIP
    zip_path.unlink()
    print(f"✓ Cleaned up {zip_path.name}")

    return extracted_dir


if __name__ == "__main__":
    # Test download
    from pathlib import Path
    output_dir = Path(__file__).parent.parent / "data" / "raw"
    extracted_path = download_bdc_dataset(output_dir)
    print(f"\n✓ Data ready at: {extracted_path}")
