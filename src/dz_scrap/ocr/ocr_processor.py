# src/dz_scrap/ocr/ocr_processor.py

import logging
from pathlib import Path
import pytesseract
from pdf2image import convert_from_path
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class OcrProcessor:
    """
    Handles the OCR process for a single PDF file.
    Converts PDF pages to images and uses Tesseract to extract text.
    """
    def __init__(self, language: str = 'fra+ara'):
        """
        Initializes the OCR processor.

        Args:
            language (str): The language string for Tesseract (e.g., 'fra' for French,
                            'ara' for Arabic, 'fra+ara' for both).
        """
        self.language = language
        logging.info(f"OCR Processor initialized for languages: {self.language}")

    def process_pdf(self, pdf_path: Path) -> str:
        """
        Performs OCR on an entire PDF file and returns the extracted text.

        Args:
            pdf_path (Path): The path to the PDF file.

        Returns:
            str: The concatenated text extracted from all pages of the PDF.
        """
        if not pdf_path.exists():
            logging.error(f"PDF file not found at: {pdf_path}")
            return ""

        logging.info(f"Starting OCR process for: {pdf_path.name}")
        full_text = []

        try:
            # Convert PDF to a list of PIL images
            # dpi=300 is a good balance of quality and processing time
            images = convert_from_path(pdf_path, dpi=300)

            for i, image in enumerate(images):
                page_num = i + 1
                logging.info(f"Processing page {page_num}/{len(images)} of {pdf_path.name}...")
                try:
                    # Use Tesseract to do OCR on the image
                    # We specify the languages to look for
                    text = pytesseract.image_to_string(image, lang=self.language)
                    full_text.append(text)
                except pytesseract.TesseractError as e:
                    logging.error(f"Tesseract error on page {page_num} of {pdf_path.name}: {e}")
                    full_text.append(f"\n--- TESSERACT ERROR ON PAGE {page_num} ---\n")

            logging.info(f"Successfully finished OCR for: {pdf_path.name}")
            return "\n\n--- NEW PAGE ---\n\n".join(full_text)

        except Exception as e:
            logging.error(f"An unexpected error occurred while processing {pdf_path}: {e}")
            return ""
