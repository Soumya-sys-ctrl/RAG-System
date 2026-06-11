"""
Retrieval layer — queries multiple indices and reranks by score.
"""
from typing import List, Dict, Any

class RetrievalManager:
    def __init__(self, vector_index, sentence_index):
        self.vector_index = vector_index
        self.sentence_index = sentence_index

    def retrieve_and_rerank(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieves from indices and balances local vs web results.
        Enforces at least 2 local results if available.
        """
        vector_results = self.vector_index.search(query, top_k=top_k)
        sentence_results = self.sentence_index.search(query, top_k=top_k)

        # Merge & deduplicate
        seen_texts = set()
        merged = []
        for r in vector_results + sentence_results:
            text_key = r["text"][:200]
            if text_key not in seen_texts:
                seen_texts.add(text_key)
                merged.append(r)

        # Separate into local and web
        local_docs = [r for r in merged if r["metadata"].get("type") != "web_search"]
        web_docs = [r for r in merged if r["metadata"].get("type") == "web_search"]

        # Sort both by score
        local_docs.sort(key=lambda x: x["score"], reverse=True)
        web_docs.sort(key=lambda x: x["score"], reverse=True)

        # Build balanced final list (prioritize local, then interleave)
        final_results = []
        
        # Take up to 3 local first
        final_results.extend(local_docs[:3])
        local_docs = local_docs[3:]
        
        # Interleave the rest
        while len(final_results) < top_k and (local_docs or web_docs):
            if web_docs:
                final_results.append(web_docs.pop(0))
            if len(final_results) < top_k and local_docs:
                final_results.append(local_docs.pop(0))
                
        # Final sort by score as last step
        final_results.sort(key=lambda x: x["score"], reverse=True)
        return final_results[:top_k]
