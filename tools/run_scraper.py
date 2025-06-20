# tools/run_scraper.py

import sys
from pathlib import Path
import argparse

# This ensures that the script can find the 'dz-scrap' module in the 'src' directory

script_dir = Path(__file__).resolve().parent  # This is the 'tools' directory
project_root = script_dir.parent  # This is your 'dz-scrap-api' directory
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))

from dz_scrap.scraping.scraper import JoradpScraper

def main():
    """Main function to run the JORADP scraper."""

    parser = argparse.ArgumentParser(description="Scrape PDFs from the Official Gazette of Algeria (joradp.dz).")
    parser.add_argument("--start-year", type=int, default=2024, help="The year to start scraping from.")
    parser.add_argument("--end-year", type=int, default=2024, help="The year to end scraping at.")
    parser.add_argument("--issues", type=int, default=100, help="Max number of issues to check per year.")

    args = parser.parse_args()

    scraper = JoradpScraper()
    scraper.scrape_by_range(
        start_year=args.start_year,
        end_year=args.end_year,
        issues_per_year=args.issues
    )

if __name__ == "__main__":
    main()
