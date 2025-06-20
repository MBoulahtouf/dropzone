# src/dz_scrap/database/db_manager.py
import sqlite3
import json
from pathlib import Path

class DBManager:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        # Table to store full documents
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT UNIQUE,
            category TEXT,
            data TEXT
        )""")
        # Table to store searchable chunks and their vector embeddings
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER,
            chunk_text TEXT,
            embedding BLOB,
            metadata TEXT,
            FOREIGN KEY (document_id) REFERENCES documents (id)
        )""")
        self.conn.commit()
    
    def get_document_by_filename(self, file_name: str) -> int | None:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM documents WHERE file_name = ?", (file_name,))
        result = cursor.fetchone()
        return result[0] if result else None
        
    def insert_document(self, file_name: str, category: str, data: list) -> int:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO documents (file_name, category, data) VALUES (?, ?, ?)",
            (file_name, category, json.dumps(data, ensure_ascii=False))
        )
        self.conn.commit()
        return cursor.lastrowid
        
    def insert_chunk(self, doc_id: int, text: str, embedding: bytes, metadata: dict):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO chunks (document_id, chunk_text, embedding, metadata) VALUES (?, ?, ?, ?)",
            (doc_id, text, embedding, json.dumps(metadata, ensure_ascii=False))
        )
        self.conn.commit()
