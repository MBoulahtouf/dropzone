# src/dz_scrap/classification/classifier.py

from typing import Dict

class DocumentClassifier:
    """
    A simple classifier to standardize and categorize document types.
    """
    def classify(self, document: Dict) -> str:
        """
        Takes a parsed document dictionary and returns a standardized category.

        Args:
            document (Dict): A single parsed document.

        Returns:
            str: A standardized category name.
        """
        doc_type = document.get("document_type", "").lower()

        if "décret" in doc_type:
            return "Decree"
        if "loi" in doc_type:
            return "Law"
        if "arrêté" in doc_type:
            return "Order"
        if "décision" in doc_type:
            return "Decision"
        if "circulaire" in doc_type:
            return "Circular"
        if "ordonnance" in doc_type:
            return "Ordinance"
        
        return "Uncategorized"
