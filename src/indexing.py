"""
Indexing layer — uses FAISS directly with Gemini embeddings via REST API.
No LlamaIndex or google-protobuf dependency.
"""
import os
import json
import pickle
import numpy as np
from typing import List, Dict, Any
from src.gemini_client import GeminiClient

class FAISSIndex:
    """Simple FAISS-based vector index."""
    
    def __init__(self, gemini: GeminiClient):
        self.gemini = gemini
        self.embeddings: np.ndarray = None
        self.documents: List[Dict[str, Any]] = []

    def add_documents(self, docs: List[Dict[str, Any]]):
        """Embed and store documents."""
        self.documents = docs
        texts = [d["text"] for d in docs]
        
        # Use batch embedding for better efficiency and rate limit handling
        emb_list = self.gemini.embed_batch(texts, task_type="RETRIEVAL_DOCUMENT")
        self.embeddings = np.array(emb_list, dtype="float32")

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Cosine-similarity search."""
        q_emb = np.array(
            self.gemini.embed(query, task_type="RETRIEVAL_QUERY"), dtype="float32"
        )
        # Normalise
        norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        normed = self.embeddings / (norms + 1e-10)
        q_norm = q_emb / (np.linalg.norm(q_emb) + 1e-10)
        
        scores = normed @ q_norm
        top_idx = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_idx:
            results.append({
                "text": self.documents[idx]["text"],
                "metadata": self.documents[idx]["metadata"],
                "score": float(scores[idx])
            })
        return results

    def save(self, path: str):
        os.makedirs(path, exist_ok=True)
        np.save(os.path.join(path, "embeddings.npy"), self.embeddings)
        with open(os.path.join(path, "documents.pkl"), "wb") as f:
            pickle.dump(self.documents, f)

    def load(self, path: str):
        self.embeddings = np.load(os.path.join(path, "embeddings.npy"))
        with open(os.path.join(path, "documents.pkl"), "rb") as f:
            self.documents = pickle.load(f)

    def append_documents(self, docs: List[Dict[str, Any]]):
        """Dynamically add new documents to the existing index."""
        texts = [d["text"] for d in docs]
        new_embs = self.gemini.embed_batch(texts, task_type="RETRIEVAL_DOCUMENT")
        new_embs_array = np.array(new_embs, dtype="float32")
        
        if self.embeddings is None:
            self.embeddings = new_embs_array
        else:
            self.embeddings = np.vstack([self.embeddings, new_embs_array])
        
        self.documents.extend(docs)


class SentenceWindowIndex:
    """
    Wraps FAISSIndex but stores sentences with surrounding context windows.
    When a sentence matches, the full window is returned.
    """
    
    def __init__(self, gemini: GeminiClient, window_size: int = 3):
        self.gemini = gemini
        self.window_size = window_size
        self.faiss_index = FAISSIndex(gemini)

    def add_documents(self, docs: List[Dict[str, Any]]):
        """Split each chunk into sentences and store with context windows."""
        windowed_docs = []
        for doc in docs:
            sentences = [s.strip() for s in doc["text"].split(".") if s.strip()]
            for i, sent in enumerate(sentences):
                start = max(0, i - self.window_size)
                end = min(len(sentences), i + self.window_size + 1)
                window = ". ".join(sentences[start:end]) + "."
                windowed_docs.append({
                    "id": len(windowed_docs),
                    "text": sent + ".",
                    "window": window,
                    "metadata": doc["metadata"]
                })
        self.faiss_index.add_documents(windowed_docs)

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        results = self.faiss_index.search(query, top_k)
        # Replace text with full window for richer context
        for r in results:
            if "window" in self.faiss_index.documents[0]:
                # Find the matching doc and use its window
                for d in self.faiss_index.documents:
                    if d["text"] == r["text"]:
                        r["text"] = d.get("window", r["text"])
                        break
        return results


class IndexingManager:
    """Manages creation of Vector and Sentence-Window indices."""
    
    def __init__(self, api_key: str):
        self.gemini = GeminiClient(api_key)

    def create_vector_index(self, docs: List[Dict[str, Any]]) -> FAISSIndex:
        idx = FAISSIndex(self.gemini)
        idx.add_documents(docs)
        return idx

    def create_sentence_window_index(self, docs: List[Dict[str, Any]]) -> SentenceWindowIndex:
        idx = SentenceWindowIndex(self.gemini)
        idx.add_documents(docs)
        return idx

    def update_indices(self, indices: Dict[str, Any], new_raw_docs: List[Dict[str, Any]], ingestion_mgr):
        """Helper to update both vector and sentence indices with new data."""
        processed_chunks = ingestion_mgr.process_documents(new_raw_docs)
        
        if "vector" in indices:
            indices["vector"].append_documents(processed_chunks)
        
        if "sentence" in indices:
            # For sentence window, we need use the Window logic
            # Re-implementing simplified append for SentenceWindow
            window_size = indices["sentence"].window_size
            windowed_docs = []
            for doc in processed_chunks:
                sentences = [s.strip() for s in doc["text"].split(".") if s.strip()]
                for i, sent in enumerate(sentences):
                    start = max(0, i - window_size)
                    end = min(len(sentences), i + window_size + 1)
                    window = ". ".join(sentences[start:end]) + "."
                    windowed_docs.append({
                        "id": len(indices["sentence"].faiss_index.documents) + len(windowed_docs),
                        "text": sent + ".",
                        "window": window,
                        "metadata": doc["metadata"]
                    })
            indices["sentence"].faiss_index.append_documents(windowed_docs)
