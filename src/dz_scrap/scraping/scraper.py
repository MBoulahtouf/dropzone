# src/dz-scrap/scraping/scraper.py

import logging
import time
import requests
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class JoradpScraper:
    """
    A scraper specifically designed to download PDF files from the
    Official Gazette of Algeria (joradp.dz).
    """
    def __init__(self, base_url: str = "https://www.joradp.dz/FTP/JO-FRANCAIS/"):
        self.base_url = base_url
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
            "Referer": "https://www.joradp.dz/HAR/Index.htm"
        }
        # Use a session object for connection pooling
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _construct_pdf_url(self, year: int, issue_number: int) -> str:
        """Constructs the direct URL for a given year and issue number."""
        # The issue number is typically zero-padded to three digits (e.g., 001, 054)
        formatted_issue = f"{issue_number:03d}"
        return f"{self.base_url}{year}/F{year}{formatted_issue}.pdf"

    def download_pdf(self, url: str, save_path: Path) -> bool:
        """
        Downloads a single PDF from a URL and saves it.

        Args:
            url (str): The URL of the PDF to download.
            save_path (Path): The local path to save the PDF file.

        Returns:
            bool: True if download was successful, False otherwise.
        """
        try:
            # Create the directory if it doesn't exist
            save_path.parent.mkdir(parents=True, exist_ok=True)

            logging.info(f"Requesting PDF from {url}...")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)

            # Check if the content is actually a PDF
            if "application/pdf" not in response.headers.get("Content-Type", ""):
                logging.warning(f"URL did not return a PDF: {url}. Content-Type: {response.headers.get('Content-Type')}")
                return False

            with open(save_path, 'wb') as f:
                f.write(response.content)

            logging.info(f"Successfully downloaded and saved to {save_path}")
            return True

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logging.warning(f"PDF not found (404 Error) at {url}. It might not exist for this issue number.")
            else:
                logging.error(f"HTTP Error downloading {url}: {e}")
            return False
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to download {url}: {e}")
            return False

    def scrape_by_range(self, start_year: int, end_year: int, issues_per_year: int = 100):
        """
        Scrapes PDFs for a given range of years and issues.

        Args:
            start_year (int): The first year in the range.
            end_year (int): The last year in the range.
            issues_per_year (int): The number of issues to check for each year.
        """
        logging.info(f"Starting scrape from {start_year} to {end_year}...")

        # Get the project's root directory to correctly resolve the data path
        project_root = Path(__file__).resolve().parents[3]
        data_dir = project_root / "data"

        for year in range(start_year, end_year + 1):
            logging.info(f"--- Processing Year: {year} ---")
            for issue in range(1, issues_per_year + 1):
                pdf_url = self._construct_pdf_url(year, issue)
                file_name = f"F{year}{issue:03d}.pdf"
                save_path = data_dir / str(year) / file_name

                if save_path.exists():
                    logging.info(f"File {save_path} already exists. Skipping.")
                    continue

                if self.download_pdf(pdf_url, save_path):
                    # Be a good citizen and wait a bit between requests
                    time.sleep(1)
                else:
                    # If we get a 404, there's a good chance we've reached the last issue for the year
                    # We'll add a small tolerance before breaking
                    if issue > 5: # A simple heuristic to avoid stopping too early
                        response = self.session.head(pdf_url) # HEAD request is lighter than GET
                        if response.status_code == 404:
                            logging.info(f"Assuming no more issues for year {year} after checking issue {issue}. Moving to next year.")
                            break
        logging.info("Scraping finished.")
