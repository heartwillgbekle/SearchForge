"""Repository layer: all SQL lives here.

Services call repositories; repositories talk to PostgreSQL through the
shared pool. API routes never contain SQL.
"""

import hashlib


def content_hash(text):
    """Stable hash of a document's content, for duplicate detection."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class DocumentRepository:
    def __init__(self, pool):
        self.pool = pool

    def save(self, filename, title, file_path, word_count, text):
        """Insert document metadata unless the content already exists.

        Returns True if inserted, False if a duplicate (same content_hash)
        was found and skipped.
        """
        digest = content_hash(text)
        with self.pool.connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM documents WHERE content_hash = %s", (digest,)
            ).fetchone()
            if row is not None:
                return False

            conn.execute(
                """
                INSERT INTO documents
                    (filename, title, file_path, content_hash, word_count)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (filename, title, file_path, digest, word_count),
            )
        return True

    def count(self):
        with self.pool.connection() as conn:
            row = conn.execute("SELECT COUNT(*) AS n FROM documents").fetchone()
        return row["n"]


class QueryRepository:
    def __init__(self, pool):
        self.pool = pool

    def save(
        self,
        query_text,
        normalized_query,
        latency_ms,
        result_count,
        cache_hit,
        ranking_method,
    ):
        with self.pool.connection() as conn:
            conn.execute(
                """
                INSERT INTO queries
                    (query_text, normalized_query, latency_ms,
                     result_count, cache_hit, ranking_method)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    query_text,
                    normalized_query,
                    latency_ms,
                    result_count,
                    cache_hit,
                    ranking_method,
                ),
            )

    def total_searches(self):
        with self.pool.connection() as conn:
            row = conn.execute("SELECT COUNT(*) AS n FROM queries").fetchone()
        return row["n"]

    def average_latency(self):
        with self.pool.connection() as conn:
            row = conn.execute(
                "SELECT AVG(latency_ms) AS avg FROM queries"
            ).fetchone()
        return round(row["avg"], 3) if row["avg"] is not None else 0.0

    def cache_hits(self):
        with self.pool.connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM queries WHERE cache_hit = TRUE"
            ).fetchone()
        return row["n"]

    def cache_misses(self):
        with self.pool.connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM queries WHERE cache_hit = FALSE"
            ).fetchone()
        return row["n"]

    def average_latency_by_cache(self, cache_hit):
        with self.pool.connection() as conn:
            row = conn.execute(
                "SELECT AVG(latency_ms) AS avg FROM queries WHERE cache_hit = %s",
                (cache_hit,),
            ).fetchone()
        return round(row["avg"], 3) if row["avg"] is not None else 0.0

    def popular_queries(self, top_k=5):
        with self.pool.connection() as conn:
            rows = conn.execute(
                """
                SELECT query_text, COUNT(*) AS n
                FROM queries
                GROUP BY query_text
                ORDER BY n DESC
                LIMIT %s
                """,
                (top_k,),
            ).fetchall()
        return [(row["query_text"], row["n"]) for row in rows]

    def slowest_queries(self, top_k=5):
        with self.pool.connection() as conn:
            rows = conn.execute(
                """
                SELECT query_text, latency_ms, result_count, created_at
                FROM queries
                ORDER BY latency_ms DESC
                LIMIT %s
                """,
                (top_k,),
            ).fetchall()
        return [dict(row) for row in rows]


class AutocompleteRepository:
    def __init__(self, pool):
        self.pool = pool

    def record(self, query_text, normalized_query):
        """Insert a new query or bump the frequency of an existing one."""
        with self.pool.connection() as conn:
            conn.execute(
                """
                INSERT INTO autocomplete_queries
                    (query_text, normalized_query, frequency, last_searched_at)
                VALUES (%s, %s, 1, now())
                ON CONFLICT (normalized_query) DO UPDATE SET
                    frequency = autocomplete_queries.frequency + 1,
                    last_searched_at = now()
                """,
                (query_text, normalized_query),
            )

    def all_queries(self):
        """Every stored query with its frequency and last-searched time."""
        with self.pool.connection() as conn:
            rows = conn.execute(
                """
                SELECT query_text, normalized_query, frequency, last_searched_at
                FROM autocomplete_queries
                """
            ).fetchall()
        return [dict(row) for row in rows]


class IndexMetadataRepository:
    def __init__(self, pool):
        self.pool = pool

    def save(self, documents_indexed, unique_terms, total_postings, ranking_method):
        with self.pool.connection() as conn:
            conn.execute(
                """
                INSERT INTO index_metadata
                    (id, documents_indexed, unique_terms,
                     total_postings, ranking_method, last_indexed_at)
                VALUES (1, %s, %s, %s, %s, now())
                ON CONFLICT (id) DO UPDATE SET
                    documents_indexed = excluded.documents_indexed,
                    unique_terms      = excluded.unique_terms,
                    total_postings    = excluded.total_postings,
                    ranking_method    = excluded.ranking_method,
                    last_indexed_at   = now()
                """,
                (documents_indexed, unique_terms, total_postings, ranking_method),
            )

    def get(self):
        with self.pool.connection() as conn:
            row = conn.execute(
                "SELECT * FROM index_metadata WHERE id = 1"
            ).fetchone()
        return dict(row) if row else None
