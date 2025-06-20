# tools/run_full_pipeline.py

import sys
import argparse
from pathlib import Path
import time
import json
import logging
from functools import partial
from multiprocessing import Pool, cpu_count

# --- Setup ---
# Configure logging for clear output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)

# Add the 'src' directory to the Python path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))

# Import all necessary processors from the application's modules
from dz_scrap.scraping.scraper import JoradpScraper
from dz_scrap.ocr.ocr_processor import OcrProcessor
from dz_scrap.parsing.parser import LegalParser
from dz_scrap.classification.classifier import DocumentClassifier
from dz_scrap.rag.chunker import DocumentChunker


# --- Encapsulated OCR Worker Function for Multiprocessing ---
def ocr_worker(pdf_path: Path, data_dir: Path, force_rerun: bool) -> Path | None:
    """A single unit of work for the OCR process, designed to be run in parallel."""
    try:
        ocr_processor = OcrProcessor(language='fra+ara')
        relative_path = pdf_path.relative_to(data_dir)
        txt_output_path = data_dir / "processed_text" / relative_path.with_suffix(".txt")
        
        if not force_rerun and txt_output_path.exists():
            logging.info(f"Text file exists for {pdf_path.name}, skipping OCR.")
            return txt_output_path
        
        logging.info(f"Performing OCR on {pdf_path.name}...")
        txt_output_path.parent.mkdir(parents=True, exist_ok=True)
        extracted_text = ocr_processor.process_pdf(pdf_path)
        
        if extracted_text:
            with open(txt_output_path, 'w', encoding='utf-8') as f:
                f.write(extracted_text)
            logging.info(f"Successfully saved text to {txt_output_path.name}")
            return txt_output_path
        else:
            logging.warning(f"Failed to extract text from {pdf_path.name}.")
            return None
    except Exception as e:
        logging.error(f"Error processing {pdf_path.name} in a worker process: {e}")
        return None

# --- Pipeline Step Functions ---

def run_scraping(start_year: int, end_year: int, issues_per_year: int, data_dir: Path) -> list[Path]:
    """
    Runs the scraping process and returns a list of downloaded PDF paths.
    """
    logging.info("--- STEP 1: Starting Scraping Process ---")
    scraper = JoradpScraper()
    # Modify the scraper to return the paths of the files it downloads
    # For now, we'll scrape and then find the files. A future improvement
    # would be for the scraper to directly return the list of downloaded files.
    scraper.scrape_by_range(start_year, end_year, issues_per_year)
    
    # Return all PDF files within the specified year range
    all_pdfs = []
    for year in range(start_year, end_year + 1):
        year_dir = data_dir / str(year)
        if year_dir.exists():
            all_pdfs.extend(list(year_dir.glob("*.pdf")))
    logging.info(f"Scraping complete. Found {len(all_pdfs)} PDFs in the target year range.")
    return sorted(all_pdfs)
    
def run_ocr(pdf_paths: list[Path], data_dir: Path, force_rerun: bool) -> list[Path]:
    """
    Runs OCR on a list of PDFs and returns a list of generated text file paths.
    """
    logging.info(f"--- STEP 2: Starting OCR Process on {len(pdf_paths)} files ---")
    ocr_processor = OcrProcessor(language='fra+ara')
    txt_output_paths = []
    
    for pdf_path in pdf_paths:
        relative_path = pdf_path.relative_to(data_dir)
        txt_output_path = data_dir / "processed_text" / relative_path.with_suffix(".txt")
        txt_output_paths.append(txt_output_path)
        
        if not force_rerun and txt_output_path.exists():
            logging.info(f"Text file exists for {pdf_path.name}, skipping OCR.")
            continue
        
        logging.info(f"Performing OCR on {pdf_path.name}...")
        txt_output_path.parent.mkdir(parents=True, exist_ok=True)
        extracted_text = ocr_processor.process_pdf(pdf_path)
        
        if extracted_text:
            with open(txt_output_path, 'w', encoding='utf-8') as f:
                f.write(extracted_text)
            logging.info(f"Successfully saved text to {txt_output_path.name}")
        else:
            logging.warning(f"Failed to extract text from {pdf_path.name}.")
            
    return txt_output_paths

def run_parsing(txt_paths: list[Path], data_dir: Path, force_rerun: bool) -> list[Path]:
    """
    Parses a list of text files and returns a list of generated JSON file paths.
    """
    logging.info(f"--- STEP 3: Starting Parsing & Classification on {len(txt_paths)} files ---")
    legal_parser = LegalParser()
    classifier = DocumentClassifier()
    json_output_paths = []
    for txt_path in txt_paths:
        if not txt_path.exists(): continue
        relative_path = txt_path.relative_to(data_dir / "processed_text")
        json_output_path = data_dir / "structured_json" / relative_path.with_suffix(".json")
        json_output_paths.append(json_output_path)
        if not force_rerun and json_output_path.exists(): continue
        with open(txt_path, 'r', encoding='utf-8') as f: raw_text = f.read()
        structured_data = legal_parser.process_full_gazette(raw_text)
        if structured_data:
            for doc in structured_data: doc['category'] = classifier.classify(doc)
            json_output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(json_output_path, 'w', encoding='utf-8') as f: json.dump(structured_data, f, ensure_ascii=False, indent=4)
    return json_output_paths

def run_rag_prep(json_paths: list[Path], data_dir: Path, force_rerun: bool) -> list[Path]:
    """
    Chunks structured JSON files and returns a list of generated chunk file paths.
    """
    logging.info(f"--- STEP 4: Starting RAG Preparation on {len(json_paths)} files ---")
    chunker = DocumentChunker()
    chunk_output_paths = []
    for json_path in json_paths:
        if not json_path.exists(): continue
        relative_path = json_path.relative_to(data_dir / "structured_json")
        chunk_output_path = data_dir / "rag_chunks" / relative_path.with_suffix(".chunks.json")
        chunk_output_paths.append(chunk_output_path)
        if not force_rerun and chunk_output_path.exists(): continue
        with open(json_path, 'r', encoding='utf-8') as f: structured_data = json.load(f)
        all_chunks = [chunk for document in structured_data for chunk in chunker.chunk_document(document)]
        if all_chunks:
            chunk_output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(chunk_output_path, 'w', encoding='utf-8') as f: json.dump(all_chunks, f, ensure_ascii=False, indent=4)
    return chunk_output_paths

# --- Main Orchestrator ---

def main():
    """Main function to orchestrate the full data processing pipeline."""
    parser = argparse.ArgumentParser(description="Full data processing pipeline for the Algerian Official Gazette.")
    parser.add_argument("--start-year", type=int, default=2024, help="The year to start scraping from.")
    parser.add_argument("--end-year", type=int, default=2024, help="The year to end scraping at.")
    parser.add_argument("--issues-per-year", type=int, default=100, help="Max number of issues to check per year during scraping.")
    parser.add_argument("--limit", type=int, default=0, help="Limit the number of files to process in each step (0 for no limit).")
    parser.add_argument("--skip-scraping", action="store_true", help="Skip the scraping step and use existing PDFs.")
    parser.add_argument("--force-rerun", action="store_true", help="Force re-processing of files even if output already exists.")
    
    args = parser.parse_args()
    
    pipeline_start_time = time.time()
    data_dir = project_root / "data"
    
    # --- Step 1: Scraping ---
    if not args.skip_scraping:
        run_scraping(args.start_year, args.end_year, args.issues_per_year, data_dir)
    else:
        logging.info("--- SKIPPING SCRAPING STEP ---")

    # --- Prepare list of files to process ---
    all_pdfs = []
    for year in range(args.start_year, args.end_year + 1):
        year_dir = data_dir / str(year)
        if year_dir.exists():
            all_pdfs.extend(list(year_dir.glob("*.pdf")))
    
    if not all_pdfs:
        logging.error("No PDFs found to process. Please run the scraper first or check the data directory.")
        return
        
    files_to_process = sorted(all_pdfs)
    if args.limit > 0:
        files_to_process = files_to_process[:args.limit]
        logging.info(f"Processing a limit of {args.limit} files.")

    # --- Execute subsequent pipeline steps ---
    txt_files = run_ocr(files_to_process, data_dir, args.force_rerun)
    json_files = run_parsing(txt_files, data_dir, args.force_rerun)
    run_rag_prep(json_files, data_dir, args.force_rerun)
    
    pipeline_end_time = time.time()
    logging.info(f"--- FULL PIPELINE COMPLETED in {pipeline_end_time - pipeline_start_time:.2f} seconds ---")


if __name__ == "__main__":
    main()
