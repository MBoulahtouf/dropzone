# tools/run_parser.py

import sys
import argparse
from pathlib import Path
import json
import time

# Add the 'src' directory to the Python path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))

from dz_scrap.parsing.parser import LegalParser
from dz_scrap.classification.classifier import DocumentClassifier # Add this import

def main():
    """Main function to find processed text files and run the parser on them."""
    parser = argparse.ArgumentParser(description="Parse raw text from Algerian Gazette files into structured JSON.")
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit the number of text files to process (0 for no limit). Useful for testing."
    )
    args = parser.parse_args()

    data_dir = project_root / "data"
    input_dir = data_dir / "processed_text"
    output_dir = data_dir / "structured_json"
    output_dir.mkdir(parents=True, exist_ok=True)

    text_files = sorted(list(input_dir.glob("**/*.txt")))

    if not text_files:
        print(f"No text files found in '{input_dir}'. Run the OCR script first.")
        return

    if args.limit > 0:
        text_files = text_files[:args.limit]

    print(f"Found {len(text_files)} text file(s) to parse.")

    legal_parser = LegalParser()
    classifier = DocumentClassifier()
    start_time = time.time()

    for i, txt_path in enumerate(text_files):
        print("-" * 50)
        print(f"Parsing file {i + 1}/{len(text_files)}: {txt_path.name}")

        with open(txt_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()

        structured_data = legal_parser.process_full_gazette(raw_text)

        if structured_data:
            # Add classification category to each document
            for doc in structured_data:
                doc['category'] = classifier.classify(doc)
  
            relative_path = txt_path.relative_to(input_dir)
            json_output_path = (output_dir / relative_path).with_suffix(".json")
            json_output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(json_output_path, 'w', encoding='utf-8') as f:
                json.dump(structured_data, f, ensure_ascii=False, indent=4)
            
            print(f"Successfully found, parsed, and classified {len(structured_data)} document(s).")
            print(f"Saved structured JSON to {json_output_path}")
        else:
            print(f"Could not extract any structured documents from {txt_path.name}.")


    end_time = time.time()
    print("-" * 50)
    print(f"Parsing completed for {len(text_files)} file(s) in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    main()
