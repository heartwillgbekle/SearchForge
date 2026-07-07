"""Bootstraps and holds the search engine components.

This is the single place that wires the engine together, so both the
API routes and the CLI share one construction path. Routes call methods
here; persistence goes through the repository layer (never inline SQL).
"""

import time

from . import config
from .db.connection import DatabasePool
from .db.repositories import (
    AutocompleteRepository,
    DocumentRepository,
    IndexMetadataRepository,
    QueryRepository,
)
from .engine.analytics import Analytics
from .engine.autocomplete import QueryTrie
from .engine.cache import SearchCache, normalize_query
from .engine.document_loader import load_documents
from .engine.indexer import InvertedIndex
from .engine.ranker import DEFAULT_RANKING, get_ranker
from .engine.searcher import Searcher


def _total_postings(index):
    return sum(len(postings) for postings in index.index.values())


class SearchEngine:
    def __init__(self, documents_dir=None, database_url=None):
        self.documents_dir = str(documents_dir or config.DOCUMENTS_DIR)
        self.database_url = database_url or config.DATABASE_URL

        self.index = InvertedIndex()
        self.searcher = None
        self.cache = None
        self.autocomplete = QueryTrie()

        # Persistence.
        self.pool = None
        self.documents_repo = None
        self.query_repo = None
        self.autocomplete_repo = None
        self.index_meta_repo = None
        self.analytics = None

    def bootstrap(self):
        """Load documents, build the index, and connect storage.

        The inverted index is rebuilt in memory on every startup (fine for
        MVP). Document metadata, query analytics, autocomplete history, and
        index metadata are persisted to PostgreSQL.
        """
        documents = load_documents(self.documents_dir)

        self.index = InvertedIndex()
        self.index.build(documents)
        self.searcher = Searcher(self.index)

        # Connect PostgreSQL and wire the repositories.
        self.pool = DatabasePool(self.database_url)
        self.pool.init_schema()
        self.documents_repo = DocumentRepository(self.pool)
        self.query_repo = QueryRepository(self.pool)
        self.autocomplete_repo = AutocompleteRepository(self.pool)
        self.index_meta_repo = IndexMetadataRepository(self.pool)
        self.analytics = Analytics(self.query_repo)

        self.cache = SearchCache()
        # The index was just (re)built, so any cached responses are stale.
        self.cache.clear()

        # Rebuild the autocomplete Trie from persisted history so suggestions
        # survive restarts.
        self.autocomplete = QueryTrie()
        for record in self.autocomplete_repo.all_queries():
            self.autocomplete.insert(
                record["query_text"],
                frequency=record["frequency"],
                last_searched=record["last_searched_at"],
            )

        inserted, skipped = self._save_documents_metadata()
        self.index_meta_repo.save(
            documents_indexed=self.index.total_documents(),
            unique_terms=self.index.total_terms(),
            total_postings=_total_postings(self.index),
            ranking_method=get_ranker(DEFAULT_RANKING).name,
        )
        return inserted, skipped

    def _save_documents_metadata(self):
        inserted = 0
        skipped = 0
        for file_name, text in self.index.documents.items():
            was_inserted = self.documents_repo.save(
                filename=file_name,
                title=file_name.rsplit(".", 1)[0],
                file_path=f"documents/{file_name}",
                word_count=self.index.document_lengths.get(file_name, 0),
                text=text,
            )
            if was_inserted:
                inserted += 1
            else:
                skipped += 1
        return inserted, skipped

    # ---- operations used by the API routes ------------------------------

    def search(self, query, top_k=5, ranking=None):
        ranker = get_ranker(ranking)
        ranking_key = ranker.name.lower()
        normalized = normalize_query(query)

        # Record the query for autocomplete (Trie + PostgreSQL), on every
        # search regardless of cache outcome.
        self.autocomplete.insert(query)
        self.autocomplete_repo.record(query, normalized)

        # 1. Cache lookup. Latency is measured around the lookup itself so a
        #    hit reflects the (much smaller) cache-serving time. The ranking
        #    method is part of the key so algorithms never mix.
        cache_start = time.perf_counter()
        cached = self.cache.get(query, ranking_key)
        if cached is not None:
            latency_ms = round((time.perf_counter() - cache_start) * 1000, 3)
            response = dict(cached)
            response["latency_ms"] = latency_ms
            response["cache_hit"] = True
            self.analytics.record_query(
                query=query,
                normalized_query=normalized,
                latency_ms=latency_ms,
                result_count=response["result_count"],
                cache_hit=True,
                ranking_method=response.get("ranking_method", ranker.name),
            )
            return response

        # 2. Cache miss: run the real search and store the response.
        response = self.searcher.search(query, top_k=top_k, ranking=ranking)
        response["result_count"] = len(response["results"])
        response["cache_hit"] = False

        self.cache.set(query, response, ranking_key)

        self.analytics.record_query(
            query=query,
            normalized_query=normalized,
            latency_ms=response["latency_ms"],
            result_count=response["result_count"],
            cache_hit=False,
            ranking_method=response["ranking_method"],
        )
        return response

    def suggest(self, prefix, limit=5):
        return self.autocomplete.suggest(prefix, limit=limit)

    def metrics(self):
        popular = self.analytics.popular_queries()
        return {
            "documents_indexed": self.index.total_documents(),
            "unique_terms": self.index.total_terms(),
            "total_postings": _total_postings(self.index),
            "average_document_length": round(
                self.index.average_document_length(), 2
            ),
            "ranking_method": get_ranker(DEFAULT_RANKING).name,
            "total_searches": self.analytics.total_searches(),
            "average_latency_ms": self.analytics.average_latency(),
            "cache_enabled": self.cache.enabled,
            "cache_hits": self.analytics.cache_hits(),
            "cache_misses": self.analytics.cache_misses(),
            "cache_hit_rate": self.analytics.cache_hit_rate(),
            "average_cached_latency_ms": self.analytics.average_cached_latency(),
            "average_uncached_latency_ms": self.analytics.average_uncached_latency(),
            "popular_queries": [
                {"query": query, "count": count} for query, count in popular
            ],
            "slowest_queries": [
                {
                    "query": record["query_text"],
                    "latency_ms": record["latency_ms"],
                }
                for record in self.analytics.slowest_queries()
            ],
        }
