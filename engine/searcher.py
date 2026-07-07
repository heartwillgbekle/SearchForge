import math
import time
from engine.preprocessor import tokenize


class Searcher:
    def __init__(self, inverted_index):
        self.inverted_index = inverted_index

    def calculate_idf(self, term):
        total_docs = self.inverted_index.total_documents()
        doc_freq = self.inverted_index.document_frequency(term)

        if doc_freq == 0:
            return 0

        return math.log((total_docs + 1) / (doc_freq + 1)) + 1

    def search(self, query, top_k=5):
        start_time = time.perf_counter()

        query_terms = tokenize(query)
        scores = {}

        for term in query_terms:
            postings = self.inverted_index.get_postings(term)
            idf = self.calculate_idf(term)

            for doc_id, frequency in postings.items():
                tf = frequency
                tf_idf_score = tf * idf

                if doc_id not in scores:
                    scores[doc_id] = 0

                scores[doc_id] += tf_idf_score

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
                "score": round(score, 4),
                "snippet": self.inverted_index.documents[doc_id][:120]
            })

        return {
            "query": query,
            "latency_ms": round(latency_ms, 3),
            "results": results
        }
