# tools/prepare_for_rag.py

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

from dz_scrap.rag.chunker import DocumentChunker

def main():
    """Finds structured JSON files and processes them into chunked files for RAG."""
    parser = argparse.ArgumentParser(description="Chunk structured JSON files for RAG systems.")
    args = parser.parse_args()

    data_dir = project_root / "data"
    input_dir = data_dir / "structured_json"
    output_dir = data_dir / "rag_chunks"
    output_dir.mkdir(parents=True, exist_ok=True)

    json_files = sorted(list(input_dir.glob("**/*.json")))

    if not json_files:
        print(f"No structured JSON files found in '{input_dir}'. Run the parser first.")
        return

    print(f"Found {len(json_files)} JSON file(s) to process into chunks.")

    chunker = DocumentChunker()
    start_time = time.time()
    total_chunks = 0

    for i, json_path in enumerate(json_files):
        print("-" * 50)
        print(f"Chunking file {i + 1}/{len(json_files)}: {json_path.name}")

        with open(json_path, 'r', encoding='utf-8') as f:
            structured_data = json.load(f)

        all_chunks = []
        for document in structured_data:
            for chunk in chunker.chunk_document(document):
                all_chunks.append(chunk)

        if all_chunks:
            total_chunks += len(all_chunks)
            relative_path = json_path.relative_to(input_dir)
            chunk_output_path = (output_dir / relative_path).with_suffix(".chunks.json")
            chunk_output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(chunk_output_path, 'w', encoding='utf-8') as f:
                json.dump(all_chunks, f, ensure_ascii=False, indent=4)
            
            print(f"Successfully created {len(all_chunks)} chunks.")
            print(f"Saved chunked JSON to {chunk_output_path}")

    end_time = time.time()
    print("-" * 50)
    print(f"Chunking completed. Created a total of {total_chunks} chunks from {len(json_files)} file(s) in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    main()
