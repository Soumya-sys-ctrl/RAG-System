"""
Generation layer — uses Gemini REST API for answer generation with citations.
"""
from typing import List, Dict, Any
from src.gemini_client import GeminiClient

class GenerationManager:
    def __init__(self, api_key: str):
        self.gemini = GeminiClient(api_key)

    def generate_response(self, query: str, context_nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
        context_str = ""
        citations = []
        for i, node in enumerate(context_nodes):
            source = node["metadata"].get("source", "Unknown")
            page = node["metadata"].get("page", "")
            label = f"[{i+1}] {source} (Page {page})" if page else f"[{i+1}] {source}"
            citations.append(label)
            context_str += f"Context {i+1}:\n{node['text']}\n\n"

        prompt = f"""You are an advanced enterprise RAG assistant.
Based on the provided contexts, answer the user's question accurately.
Explicitly cite your sources using the numbers [1], [2], etc., where applicable.

Contexts:
{context_str}

User Question: {query}

Response:"""

        answer = self.gemini.generate(prompt)
        return {"answer": answer, "citations": citations}

    def format_citations(self, citations: List[str]) -> str:
        return "\n".join([f"- {c}" for c in citations])
