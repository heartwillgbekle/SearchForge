"""PostgreSQL connection pool and schema initialization.

A single connection pool is shared across the app. Repositories borrow
connections from it; they never open their own. Rows come back as dicts.
"""

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .. import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id            SERIAL PRIMARY KEY,
    filename      TEXT NOT NULL,
    title         TEXT,
    file_path     TEXT,
    content_hash  TEXT NOT NULL UNIQUE,
    word_count    INTEGER NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS queries (
    id               SERIAL PRIMARY KEY,
    query_text       TEXT NOT NULL,
    normalized_query TEXT NOT NULL,
    latency_ms       REAL NOT NULL,
    result_count     INTEGER NOT NULL,
    cache_hit        BOOLEAN NOT NULL DEFAULT FALSE,
    ranking_method   TEXT NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_queries_normalized ON queries (normalized_query);

CREATE TABLE IF NOT EXISTS autocomplete_queries (
    id               SERIAL PRIMARY KEY,
    query_text       TEXT NOT NULL,
    normalized_query TEXT NOT NULL UNIQUE,
    frequency        INTEGER NOT NULL DEFAULT 1,
    last_searched_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS index_metadata (
    id               INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    documents_indexed INTEGER NOT NULL,
    unique_terms      INTEGER NOT NULL,
    total_postings    INTEGER NOT NULL,
    ranking_method    TEXT NOT NULL,
    last_indexed_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


class DatabasePool:
    def __init__(self, database_url=None):
        url = database_url or config.DATABASE_URL
        if not url:
            raise RuntimeError(
                "DATABASE_URL is not set. Add it to backend/.env "
                "(postgresql://user:pass@host:5432/dbname)."
            )
        self.pool = ConnectionPool(
            conninfo=url,
            min_size=1,
            max_size=10,
            kwargs={"row_factory": dict_row},
            open=True,
        )

    def init_schema(self):
        with self.pool.connection() as conn:
            conn.execute(SCHEMA)

    def connection(self):
        """Context manager yielding a pooled connection."""
        return self.pool.connection()

    def close(self):
        self.pool.close()
