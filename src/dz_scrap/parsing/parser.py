# src/dz_scrap/parsing/parser.py

import logging
import re
from typing import Dict, List, Optional

# Import our custom patterns
from dz_scrap.parsing.patterns import (
    DOCUMENT_START_PATTERN,
    DOCUMENT_HEADER_PATTERN,
    ARTICLE_PATTERN,
    INDIVIDUAL_DECISION_PATTERN,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class LegalParser:
    """
    Parses raw text from the Algerian Official Gazette into structured data.
    """
    def _pre_clean_gazette(self, text: str) -> str:
        """Removes page-level artifacts before any other processing."""
        text = re.sub(r'--- NEW PAGE ---', '', text)
        text = re.sub(r'\n\s*9 Joumada Ethania 1446\n.*', '', text)
        text = re.sub(r'\n\s*JOURNAL OFFICIEL DE LA REPUBLIQUE ALGERIENNE N° \d+', '', text)
        return text

    def _clean_field(self, text: str) -> str:
        """Performs final cleaning on an extracted field."""
        text = text.replace('\n', ' ').strip()
        text = re.sub(r'\s+', ' ', text)
        return text.lstrip('.- ').strip()

    def _find_content_start(self, text: str) -> str:
        """Finds the start of the main content after the SOMMAIRE."""
        # We start parsing from "DECISIONS" or the first major heading after the table of contents
        parts = re.split(r'SOMMAIRE(?: \(suite\))?', text, maxsplit=1, flags=re.IGNORECASE)
        if len(parts) > 1:
            return parts[1]
        logging.warning("SOMMAIRE section not found. Attempting to parse from beginning.")
        return text

    def parse_articles(self, text: str) -> List[Dict[str, str]]:
        """Finds and parses all articles in a given text block."""
        articles = []
        for match in ARTICLE_PATTERN.finditer(text):
            data = match.groupdict()
            articles.append({
                "number": self._clean_field(data.get("number", "")),
                "content": self._clean_field(data.get("content", ""))
            })
        return articles

    def parse_document(self, doc_text: str) -> Optional[Dict]:
        """
        Parses a single legal document's text to extract its metadata and articles.
        """
        header_match = DOCUMENT_HEADER_PATTERN.search(doc_text)
        is_individual = False
        if not header_match:
            header_match = INDIVIDUAL_DECISION_PATTERN.search(doc_text)
            is_individual = True

        if not header_match:
            return None

        header_data = header_match.groupdict()
        
        document_type = self._clean_field(header_data.get("type", "N/A"))
        official_number = self._clean_field(header_data.get("number", "N/A"))
        date = self._clean_field(header_data.get("date", "N/A"))
        title = self._clean_field(header_data.get("title", "N/A"))

        # If it's a simple individual decision, it has no articles by definition
        if is_individual:
            articles = []
        else:
            # DEFINITIVE FIX for "Missing Article 1":
            # The articles start AFTER the header. We find where the header match ends
            # and pass the remainder of the text to the article parser.
            # This was the original logic, but it needed the header pattern to be correct.
            # Now that the header pattern correctly stops before "Article 1", this works.
            article_text_block = doc_text[header_match.end():]
            articles = self.parse_articles(article_text_block)

        # Final validation
        if title == "N/A" and not articles:
            return None
            
        return {
            "document_type": document_type,
            "official_number": official_number,
            "date": date,
            "title": title,
            "articles": articles,
        }

    def process_full_gazette(self, full_text: str) -> List[Dict]:
        """
        Processes the entire text of a gazette, splitting it into individual
        legal documents and parsing each one.
        """
        cleaned_gazette_text = self._pre_clean_gazette(full_text)
        main_content = self._find_content_start(cleaned_gazette_text)
        
        starts = [match.start() for match in DOCUMENT_START_PATTERN.finditer(main_content)]
        if not starts:
            return []

        doc_texts = []
        for i in range(len(starts)):
            start_pos = starts[i]
            end_pos = starts[i+1] if i + 1 < len(starts) else len(main_content)
            doc_texts.append(main_content[start_pos:end_pos])

        parsed_documents = []
        for i, doc_text in enumerate(doc_texts):
            logging.info(f"--- Parsing potential document segment #{i+1} ---")
            parsed_doc = self.parse_document(doc_text)
            if parsed_doc:
                # Filter out low-quality results that are just titles without articles
                if parsed_doc["official_number"] == "N/A" and not parsed_doc["articles"]:
                    # Check if it's a personnel change decree, which is valid without articles
                    if "nomination" in parsed_doc["title"] or "mettant fin" in parsed_doc["title"]:
                        parsed_documents.append(parsed_doc)
                    else:
                        logging.warning(f"Skipping document with no number and no articles: {parsed_doc['title']}")
                else:
                    parsed_documents.append(parsed_doc)
        
        return parsed_documents
