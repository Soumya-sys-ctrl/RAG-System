"""
Gemini REST API Client — bypasses google-protobuf issues on Python 3.14.
Uses the Gemini REST API directly via `requests`.
"""
import requests
import json
import time
from typing import List, Optional

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"

class GeminiClient:
    def __init__(self, api_key: str, model: str = "gemini-flash-latest"):
        self.api_key = api_key
        self.model = model

    def _request_with_retry(self, method: str, url: str, **kwargs) -> requests.Response:
        max_retries = 10
        base_delay = 2 # Increased base delay
        for i in range(max_retries):
            resp = requests.request(method, url, **kwargs)
            if resp.status_code == 429:
                # Add jitter to delay
                import random
                delay = base_delay * (2 ** i) + random.uniform(0, 1)
                print(f"⚠️ Rate limited (429). Retrying in {delay:.1f}s...")
                time.sleep(delay)
                continue
            resp.raise_for_status()
            return resp
        resp.raise_for_status()
        return resp

    # ── Text Generation ──────────────────────────────────────────────
    def generate(self, prompt: str, temperature: float = 0.1) -> str:
        url = f"{GEMINI_API_BASE}/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature}
        }
        resp = self._request_with_retry("POST", url, json=payload, timeout=60)
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    # ── Embeddings ───────────────────────────────────────────────────
    def embed(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> List[float]:
        url = f"{GEMINI_API_BASE}/models/gemini-embedding-001:embedContent?key={self.api_key}"
        payload = {
            "model": "models/gemini-embedding-001",
            "content": {"parts": [{"text": text}]},
            "taskType": task_type
        }
        resp = self._request_with_retry("POST", url, json=payload, timeout=60)
        data = resp.json()
        return data["embedding"]["values"]

    def embed_batch(self, texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT") -> List[List[float]]:
        # Max batch size for Gemini is usually 100
        batch_size = 100
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            url = f"{GEMINI_API_BASE}/models/gemini-embedding-001:batchEmbedContents?key={self.api_key}"
            requests_payload = []
            for text in batch:
                requests_payload.append({
                    "model": "models/gemini-embedding-001",
                    "content": {"parts": [{"text": text}]},
                    "taskType": task_type
                })
            payload = {"requests": requests_payload}
            resp = self._request_with_retry("POST", url, json=payload, timeout=60)
            data = resp.json()
            all_embeddings.extend([e["values"] for e in data["embeddings"]])
        return all_embeddings

    # ── Health Check ─────────────────────────────────────────────────
    def health_check(self) -> bool:
        try:
            result = self.generate("Say 'OK' in one word.", temperature=0.0)
            return len(result.strip()) > 0
        except Exception:
            return False
