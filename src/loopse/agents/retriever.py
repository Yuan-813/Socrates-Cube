from src.loopse.kb.vector_store import vector_store
from typing import List, Dict

class RetrieverAgent:
    
    def search_knowledge(self, query: str, n_results: int = 3) -> List[Dict]:
        results = vector_store.search("course_docs", query, n_results)
        return self._format_results(results, "course_docs")
    
    def search_misconceptions(self, query: str, n_results: int = 3) -> List[Dict]:
        results = vector_store.search("misconceptions", query, n_results)
        return self._format_results(results, "misconceptions")
    
    def search_all(self, query: str) -> Dict:
        return {
            "knowledge": self.search_knowledge(query),
            "misconceptions": self.search_misconceptions(query)
        }
    
    def _format_results(self, results: Dict, source: str) -> List[Dict]:
        if not results or not results.get("documents") or not results["documents"][0]:
            return []
        formatted = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            formatted.append({
                "content": doc,
                "metadata": meta,
                "relevance": 1 - dist if dist is not None else 0.0,
                "source": source
            })
        return formatted

retriever_agent = RetrieverAgent()
