"""
Ingestion layer — native PDF/CSV loading + text splitting.
No LangChain dependency (avoids Pydantic V1 / Python 3.14 issues).
"""
import os
import csv
from typing import List, Dict, Any
from pypdf import PdfReader

class IngestionManager:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def load_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        reader = PdfReader(file_path)
        pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                pages.append({
                    "text": text,
                    "metadata": {"source": os.path.basename(file_path), "page": i}
                })
        return pages

    def load_csv(self, file_path: str) -> List[Dict[str, Any]]:
        docs = []
        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                text = " | ".join(f"{k}: {v}" for k, v in row.items())
                docs.append({
                    "text": text,
                    "metadata": {"source": os.path.basename(file_path), "row": i}
                })
        return docs

    def _split_text(self, text: str) -> List[str]:
        """Recursive character text splitter (simple implementation)."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += self.chunk_size - self.chunk_overlap
        return [c for c in chunks if c.strip()]

    def process_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Chunk all documents."""
        processed = []
        for doc in documents:
            chunks = self._split_text(doc["text"])
            for chunk in chunks:
                processed.append({
                    "id": len(processed),
                    "text": chunk,
                    "metadata": doc["metadata"]
                })
        return processed
