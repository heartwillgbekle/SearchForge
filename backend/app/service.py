"""Bootstraps and holds the search engine components.

This is the single place that wires the engine together, so both the
API routes and the CLI share one construction path. Routes should call
methods here rather than touching the engine internals directly.
"""

from . import config
from .engine.analytics import Analytics
from .engine.database import Database
from .engine.document_loader import load_documents
from .engine.indexer import InvertedIndex
from .engine.searcher import Searcher


def _total_postings(index):
    return sum(len(postings) for postings in index.index.values())


class SearchEngine:
    def __init__(self, documents_dir=None, database_path=None):
        self.documents_dir = str(documents_dir or config.DOCUMENTS_DIR)
        self.database_path = str(database_path or config.DATABASE_PATH)

        self.index = InvertedIndex()
        self.searcher = None
        self.database = None
        self.analytics = None

    def bootstrap(self):
        """Load documents, build the index, and connect storage.

        The index is rebuilt in memory on every startup (fine for MVP).
        Document and index metadata are persisted to SQLite.
        """
        documents = load_documents(self.documents_dir)

        self.index = InvertedIndex()
        self.index.build(documents)

        self.searcher = Searcher(self.index)
        self.database = Database(self.database_path)
        self.analytics = Analytics(self.database)

        inserted, skipped = self._save_documents_metadata()
        self.database.save_index_metadata(
            total_documents=self.index.total_documents(),
            total_terms=self.index.total_terms(),
            total_postings=_total_postings(self.index),
        )
        return inserted, skipped

    def _save_documents_metadata(self):
        inserted = 0
        skipped = 0
        for file_name, text in self.index.documents.items():
            was_inserted = self.database.save_document(
                file_name=file_name,
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

    def search(self, query, top_k=5):
        response = self.searcher.search(query, top_k=top_k)
        self.analytics.record_query(
            query=query,
            latency_ms=response["latency_ms"],
            result_count=len(response["results"]),
        )
        response["result_count"] = len(response["results"])
        return response

    def metrics(self):
        popular = self.analytics.popular_queries()
        return {
            "documents_indexed": self.index.total_documents(),
            "unique_terms": self.index.total_terms(),
            "total_postings": _total_postings(self.index),
            "total_searches": self.analytics.total_searches(),
            "average_latency_ms": self.analytics.average_latency(),
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
