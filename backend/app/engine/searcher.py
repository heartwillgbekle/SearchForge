import time
from .preprocessor import tokenize
from .ranker import get_ranker


class Searcher:
    def __init__(self, inverted_index):
        self.inverted_index = inverted_index

    def make_snippet(self, text, query_terms, window=50):
        lower_text = text.lower()

        match_pos = -1
        for term in query_terms:
            position = lower_text.find(term)
            if position != -1:
                match_pos = position
                break

        # No query term found in the document: fall back to the start.
        if match_pos == -1:
            return text[:120]

        start = max(0, match_pos - window)
        end = min(len(text), match_pos + window)

        snippet = text[start:end]

        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."

        return snippet

    def search(self, query, top_k=5, ranking=None):
        start_time = time.perf_counter()

        query_terms = tokenize(query)
        ranker = get_ranker(ranking)

        # Retrieval + scoring: the ranker decides how documents score.
        scores = ranker.score(query_terms, self.inverted_index)

        ranked_results = sorted(
            scores.items(),
            key=lambda item: item[1],
            reverse=True
        )

        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000

        results = []

        for doc_id, score in ranked_results[:top_k]:
            document_text = self.inverted_index.documents[doc_id]
            results.append({
                "document": doc_id,
                "score": round(score, 4),
                "snippet": self.make_snippet(document_text, query_terms)
            })

        return {
            "query": query,
            "latency_ms": round(latency_ms, 3),
            "ranking_method": ranker.name,
            "results": results
        }
