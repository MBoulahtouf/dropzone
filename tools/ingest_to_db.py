# tools/ingest_to_db.py
import sys
import json
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))

from dz_scrap.database.db_manager import DBManager

def main():
    print("--- Starting Ingestion to Database ---")
    data_dir = project_root / "data"
    db_path = data_dir / "legal_data.db"
    
    # Initialize database and embedding model
    db_manager = DBManager(db_path)
    print("Loading sentence-transformer model...")
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    print("Model loaded.")
    
    json_files = sorted(list((data_dir / "structured_json").glob("**/*.json")))
    chunk_files = sorted(list((data_dir / "rag_chunks").glob("**/*.chunks.json")))

    # Ingest full documents first
    for json_path in json_files:
        if db_manager.get_document_by_filename(json_path.name):
            print(f"Document {json_path.name} already in DB. Skipping.")
            continue
        print(f"Ingesting document: {json_path.name}")
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Use the category of the first document as representative
            category = data[0].get('category', 'Uncategorized') if data else 'Uncategorized'
            db_manager.insert_document(json_path.name, category, data)
            
    # Ingest chunks and create embeddings
    for chunk_path in chunk_files:
        print(f"Processing chunks from: {chunk_path.name}")
        doc_id = db_manager.get_document_by_filename(chunk_path.name.replace('.chunks.json', '.json'))
        if not doc_id:
            print(f"Warning: No parent document found in DB for {chunk_path.name}. Skipping.")
            continue
            
        with open(chunk_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        texts_to_embed = [chunk['text'] for chunk in chunks]
        print(f"Creating {len(texts_to_embed)} embeddings...")
        embeddings = model.encode(texts_to_embed, show_progress_bar=True)
        
        print("Inserting chunks and embeddings into database...")
        for i, chunk in enumerate(chunks):
            embedding_bytes = embeddings[i].astype(np.float32).tobytes()
            db_manager.insert_chunk(doc_id, chunk['text'], embedding_bytes, chunk['metadata'])
            
    print("--- Ingestion Complete ---")

if __name__ == "__main__":
    main()
