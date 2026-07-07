import hashlib
import sqlite3
from datetime import datetime

DEFAULT_DB_PATH = "searchforge.db"


def content_hash(text):
    """Stable hash of a document's content, used for duplicate detection."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Database:
    """SQLite persistence layer for SearchForge.

    Owns all SQL. The searcher and analytics logic never touch the
    connection directly, keeping persistence separate from search.

    Stores document metadata, query analytics, and index metadata.
    The inverted index itself stays in memory for now.
    """

    def __init__(self, db_path=DEFAULT_DB_PATH):
        self.db_path = db_path
        # check_same_thread=False keeps this usable from a future web server.
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name     TEXT NOT NULL,
                title         TEXT,
                file_path     TEXT,
                word_count    INTEGER NOT NULL,
                content_hash  TEXT NOT NULL UNIQUE,
                created_at    TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS queries (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                query_text    TEXT NOT NULL,
                latency_ms    REAL NOT NULL,
                result_count  INTEGER NOT NULL,
                cache_hit     INTEGER NOT NULL DEFAULT 0,
                created_at    TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS index_metadata (
                id             INTEGER PRIMARY KEY CHECK (id = 1),
                total_documents INTEGER NOT NULL,
                total_terms     INTEGER NOT NULL,
                total_postings  INTEGER NOT NULL,
                last_indexed_at TEXT NOT NULL
            );
            """
        )
        self._migrate()
        self.connection.commit()

    def _migrate(self):
        """Apply small schema upgrades to pre-existing databases."""
        columns = {
            row["name"]
            for row in self.connection.execute("PRAGMA table_info(queries)")
        }
        if "cache_hit" not in columns:
            self.connection.execute(
                "ALTER TABLE queries ADD COLUMN cache_hit INTEGER NOT NULL DEFAULT 0"
            )

    # ---- documents -------------------------------------------------------

    def save_document(self, file_name, title, file_path, word_count, text):
        """Insert document metadata unless its content already exists.

        Returns True if the document was inserted, False if it was a
        duplicate (same content_hash) and therefore skipped.
        """
        digest = content_hash(text)
        cursor = self.connection.execute(
            "SELECT 1 FROM documents WHERE content_hash = ?", (digest,)
        )
        if cursor.fetchone() is not None:
            return False

        self.connection.execute(
            """
            INSERT INTO documents
                (file_name, title, file_path, word_count, content_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                file_name,
                title,
                file_path,
                word_count,
                digest,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        self.connection.commit()
        return True

    # ---- index metadata --------------------------------------------------

    def save_index_metadata(self, total_documents, total_terms, total_postings):
        self.connection.execute(
            """
            INSERT INTO index_metadata
                (id, total_documents, total_terms, total_postings, last_indexed_at)
            VALUES (1, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                total_documents = excluded.total_documents,
                total_terms     = excluded.total_terms,
                total_postings  = excluded.total_postings,
                last_indexed_at = excluded.last_indexed_at
            """,
            (
                total_documents,
                total_terms,
                total_postings,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        self.connection.commit()

    # ---- queries ---------------------------------------------------------

    def save_query(self, query_text, latency_ms, result_count, cache_hit=False):
        self.connection.execute(
            """
            INSERT INTO queries
                (query_text, latency_ms, result_count, cache_hit, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                query_text,
                latency_ms,
                result_count,
                1 if cache_hit else 0,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        self.connection.commit()

    # ---- analytics reads -------------------------------------------------

    def total_searches(self):
        row = self.connection.execute(
            "SELECT COUNT(*) AS n FROM queries"
        ).fetchone()
        return row["n"]

    def average_latency(self):
        row = self.connection.execute(
            "SELECT AVG(latency_ms) AS avg FROM queries"
        ).fetchone()
        if row["avg"] is None:
            return 0.0
        return round(row["avg"], 3)

    def cache_hits(self):
        row = self.connection.execute(
            "SELECT COUNT(*) AS n FROM queries WHERE cache_hit = 1"
        ).fetchone()
        return row["n"]

    def cache_misses(self):
        row = self.connection.execute(
            "SELECT COUNT(*) AS n FROM queries WHERE cache_hit = 0"
        ).fetchone()
        return row["n"]

    def average_latency_by_cache(self, cache_hit):
        row = self.connection.execute(
            "SELECT AVG(latency_ms) AS avg FROM queries WHERE cache_hit = ?",
            (1 if cache_hit else 0,),
        ).fetchone()
        if row["avg"] is None:
            return 0.0
        return round(row["avg"], 3)

    def popular_queries(self, top_k=5):
        rows = self.connection.execute(
            """
            SELECT query_text, COUNT(*) AS n
            FROM queries
            GROUP BY query_text
            ORDER BY n DESC
            LIMIT ?
            """,
            (top_k,),
        ).fetchall()
        return [(row["query_text"], row["n"]) for row in rows]

    def slowest_queries(self, top_k=5):
        rows = self.connection.execute(
            """
            SELECT query_text, latency_ms, result_count, created_at
            FROM queries
            ORDER BY latency_ms DESC
            LIMIT ?
            """,
            (top_k,),
        ).fetchall()
        return [dict(row) for row in rows]

    def close(self):
        self.connection.close()
