import time
from engine.preprocessor import tokenize


class Searcher:
    def __init__(self, inverted_index):
        self.inverted_index = inverted_index

    def search(self, query, top_k=5):
        start_time = time.perf_counter()

        query_terms = tokenize(query)
        scores = {}

        for term in query_terms:
            postings = self.inverted_index.get_postings(term)

            for doc_id, frequency in postings.items():
                if doc_id not in scores:
                    scores[doc_id] = 0

                scores[doc_id] += frequency

        ranked_results = sorted(
            scores.items(),
            key=lambda item: item[1],
            reverse=True
        )

        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000

        results = []

        for doc_id, score in ranked_results[:top_k]:
            results.append({
                "document": doc_id,
                "score": score,
                "snippet": self.inverted_index.documents[doc_id][:120]
            })

        return {
            "query": query,
            "latency_ms": round(latency_ms, 3),
            "results": results
        }
