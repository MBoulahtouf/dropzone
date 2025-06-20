# main.py

import sys
import numpy as np
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException

project_root = Path(__file__).resolve().parent
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))


from sentence_transformers import SentenceTransformer, util
from dz_scrap.database.db_manager import DBManager

# --- Initialization ---
app = FastAPI(
    title="Algerian Law Search API",
    description="An API to search and retrieve structured legal documents from the Official Gazette of Algeria.",
    version="1.0.0"
)

# Load resources on startup
@app.on_event("startup")
def load_resources():
    print("API starting up...")
    data_dir = Path(__file__).parent / "data"
    db_path = data_dir / "legal_data.db"
    
    app.state.db_manager = DBManager(db_path)
    
    print("Loading embedding model...")
    app.state.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    
    print("Loading vectors from database into memory...")
    cursor = app.state.db_manager.conn.cursor()
    cursor.execute("SELECT id, embedding, chunk_text, metadata FROM chunks")
    
    vectors = []
    for row in cursor.fetchall():
        vectors.append({
            "id": row[0],
            "embedding": np.frombuffer(row[1], dtype=np.float32),
            "text": row[2],
            "metadata": json.loads(row[3])
        })
    app.state.vectors = vectors
    print(f"Startup complete. Loaded {len(vectors)} vectors.")

# --- API Endpoints ---
@app.get("/", tags=["General"])
def read_root():
    return {"message": "Welcome to the DropZone Law Search API"}

@app.get("/search", tags=["Search"])
def search_documents(q: str, top_k: int = 5):
    """
    Search for relevant text chunks using a natural language query.
    """
    if not hasattr(app.state, 'model'):
        raise HTTPException(status_code=503, detail="API is not ready, resources are loading.")
        
    query_embedding = app.state.model.encode(q)
    
    # Calculate cosine similarity with imported 'util'
    all_embeddings = np.array([v['embedding'] for v in app.state.vectors])
    similarities = util.cos_sim(query_embedding, all_embeddings)[0]
    
    # argsort() returns the indices that would sort the array.
    # Slicing with [-top_k:] gets the indices of the top K highest scores.
    top_k_indices = np.argsort(similarities)[-top_k:]
    # Reverse the list to get the highest score first
    top_k_indices = reversed(top_k_indices)
    
    results = []
    # top_results is a list of tuples (score, index)
    for idx in top_k_indices:
        # Get the original vector info using the index
        vector_info = app.state.vectors[idx]
        # Get the similarity score for that index
        score = similarities[idx]
        
        results.append({
            "score": float(score),
            "text": vector_info['text'],
            "metadata": vector_info['metadata']
        })
        
    return {"query": q, "results": results}

@app.get("/documents/{file_name}", tags=["Documents"])
def get_document(file_name: str):
    """
    Retrieve a full, structured legal document by its original file name (e.g., F2024081.json).
    """
    cursor = app.state.db_manager.conn.cursor()
    cursor.execute("SELECT data FROM documents WHERE file_name = ?", (file_name,))
    result = cursor.fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
        
    return json.loads(result[0])
