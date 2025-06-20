# src/dz_scrap/rag/chunker.py

from typing import Dict, List, Iterator

class DocumentChunker:
    """
    Splits structured legal documents into smaller text chunks suitable for RAG systems.
    """
    def chunk_document(self, document: Dict) -> Iterator[Dict]:
        """
        Yields text chunks from a single document's articles.

        Each chunk contains the text and metadata linking back to the source.

        Args:
            document (Dict): A single document from the structured JSON.

        Yields:
            Iterator[Dict]: A sequence of chunk dictionaries.
        """
        # Create a base metadata object for all chunks from this document
        base_metadata = {
            "source_document_type": document.get("document_type"),
            "source_official_number": document.get("official_number"),
            "source_date": document.get("date"),
            "source_category": document.get("category"),
        }

        articles = document.get("articles", [])
        
        if not articles:
            # For documents without articles (like individual decisions),
            # the title itself can be a searchable chunk.
            chunk_text = f'{document.get("document_type")}: {document.get("title")}'
            chunk = {
                "text": chunk_text,
                "metadata": {
                    **base_metadata,
                    "source_article_number": "N/A",
                }
            }
            yield chunk
        else:
            for article in articles:
                article_number = article.get("number", "N/A")
                content = article.get("content", "")

                # For this version, we'll treat each article as a single chunk.
                # A more advanced implementation could split long articles by sentences.
                chunk_text = f'Article {article_number}: {content}'

                chunk = {
                    "text": chunk_text,
                    "metadata": {
                        **base_metadata,
                        "source_article_number": article_number,
                    }
                }
                yield chunk
