# tools/run_ocr.py

import sys
import argparse
from pathlib import Path
import time

# Add the 'src' directory to the Python path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))

from dz_scrap.ocr.ocr_processor import OcrProcessor

def main():
    """Main function to find PDFs and run the OCR process on them."""
    parser = argparse.ArgumentParser(description="Run OCR on downloaded Algerian Gazette PDFs.")
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit the number of PDFs to process (0 for no limit). Useful for testing."
    )
    args = parser.parse_args()

    data_dir = project_root / "data"
    output_dir = data_dir / "processed_text"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all PDF files in the data directory and its subdirectories
    pdf_files = list(data_dir.glob("**/*.pdf"))

    if not pdf_files:
        print("No PDF files found in the 'data' directory. Run the scraper first.")
        return

    # Apply limit if specified
    if args.limit > 0:
        pdf_files = pdf_files[:args.limit]

    print(f"Found {len(pdf_files)} PDF(s) to process.")

    ocr_processor = OcrProcessor(language='fra+ara')
    start_time = time.time()

    for i, pdf_path in enumerate(pdf_files):
        print("-" * 50)
        print(f"Processing file {i + 1}/{len(pdf_files)}: {pdf_path.name}")

        # Define the output path for the .txt file
        # It will mirror the directory structure, e.g., data/processed_text/2024/F2024001.txt
        relative_path = pdf_path.relative_to(data_dir)
        txt_output_path = (output_dir / relative_path).with_suffix(".txt")

        if txt_output_path.exists():
            print(f"Output file already exists at {txt_output_path}. Skipping.")
            continue

        txt_output_path.parent.mkdir(parents=True, exist_ok=True)

        # Perform OCR
        extracted_text = ocr_processor.process_pdf(pdf_path)

        if extracted_text:
            # Save the extracted text
            with open(txt_output_path, 'w', encoding='utf-8') as f:
                f.write(extracted_text)
            print(f"Successfully saved extracted text to {txt_output_path}")
        else:
            print(f"Failed to extract text from {pdf_path.name}.")

    end_time = time.time()
    print("-" * 50)
    print(f"OCR processing completed for {len(pdf_files)} file(s) in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    main()
