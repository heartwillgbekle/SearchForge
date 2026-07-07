"""Ranking algorithms for scoring documents against a query.

Ranking is separated from retrieval so the searcher can retrieve
candidate documents and delegate scoring to a pluggable ranker. Two
rankers are provided: TF-IDF and BM25 (the default).

Each ranker exposes score(query_terms, index) -> {doc_id: score}.
"""

import math


class TfidfRanker:
    name = "TF-IDF"

    def idf(self, term, index):
        total_docs = index.total_documents()
        doc_freq = index.document_frequency(term)
        if doc_freq == 0:
            return 0.0
        # Smoothed IDF, matching the earlier TF-IDF behavior.
        return math.log((total_docs + 1) / (doc_freq + 1)) + 1

    def score(self, query_terms, index):
        scores = {}
        for term in query_terms:
            idf = self.idf(term, index)
            for doc_id, frequency in index.get_postings(term).items():
                scores[doc_id] = scores.get(doc_id, 0.0) + frequency * idf
        return scores


class BM25Ranker:
    """Okapi BM25 with the standard k1/b constants.

    k1 controls term-frequency saturation (repeated terms give
    diminishing returns); b controls how strongly document length
    normalizes the score.
    """

    name = "BM25"

    def __init__(self, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b

    def idf(self, term, index):
        total_docs = index.total_documents()
        doc_freq = index.document_frequency(term)
        if doc_freq == 0:
            return 0.0
        # BM25 IDF with +1 to keep it non-negative even for very common terms.
        return math.log(1 + (total_docs - doc_freq + 0.5) / (doc_freq + 0.5))

    def score(self, query_terms, index):
        avg_len = index.average_document_length() or 1.0
        scores = {}

        for term in query_terms:
            idf = self.idf(term, index)
            for doc_id, frequency in index.get_postings(term).items():
                doc_len = index.document_lengths.get(doc_id, 0)
                # TF component with saturation (k1) and length norm (b).
                denominator = frequency + self.k1 * (
                    1 - self.b + self.b * (doc_len / avg_len)
                )
                term_score = idf * (frequency * (self.k1 + 1)) / denominator
                scores[doc_id] = scores.get(doc_id, 0.0) + term_score

        return scores


# Registry so the searcher / API can select a ranker by name.
RANKERS = {
    "bm25": BM25Ranker(),
    "tfidf": TfidfRanker(),
}

DEFAULT_RANKING = "bm25"


def get_ranker(name=None):
    """Return a ranker by key, falling back to the default."""
    key = (name or DEFAULT_RANKING).lower()
    return RANKERS.get(key, RANKERS[DEFAULT_RANKING])
