"""Redis-backed cache for full search responses.

Caches only the search response for a normalized query. If Redis is
unreachable, the cache degrades gracefully: get() returns None and
set() is a no-op, so search still works (just uncached).
"""

import json

from .. import config


def normalize_query(query):
    """Collapse case and whitespace so equivalent queries share a key.

    "Machine  Learning" and " machine learning " both -> "machine learning"
    """
    return " ".join(query.lower().split())


def cache_key(query):
    return f"search:{normalize_query(query)}"


def _connect():
    """Return a live Redis client, or None if none is available.

    Uses fakeredis when USE_FAKE_REDIS is set (local dev without a real
    server); otherwise connects to REDIS_URL and pings to confirm.
    """
    try:
        if config.USE_FAKE_REDIS:
            import fakeredis

            return fakeredis.FakeStrictRedis(decode_responses=True)

        import redis

        client = redis.Redis.from_url(config.REDIS_URL, decode_responses=True)
        client.ping()
        return client
    except Exception as exc:  # connection refused, bad URL, missing pkg
        print(f"[cache] Redis unavailable, running uncached: {exc}")
        return None


class SearchCache:
    def __init__(self, ttl_seconds=None):
        self.ttl_seconds = ttl_seconds or config.CACHE_TTL_SECONDS
        self.client = _connect()

    @property
    def enabled(self):
        return self.client is not None

    def get(self, query):
        """Return the cached response dict for a query, or None."""
        if not self.client:
            return None
        try:
            raw = self.client.get(cache_key(query))
        except Exception:
            return None
        if raw is None:
            return None
        return json.loads(raw)

    def set(self, query, response):
        """Store a search response with the configured expiration."""
        if not self.client:
            return
        try:
            self.client.set(
                cache_key(query),
                json.dumps(response),
                ex=self.ttl_seconds,
            )
        except Exception:
            # Caching is best-effort; never fail a search over it.
            pass

    def clear(self):
        """Drop all cached search responses (e.g. after reindexing)."""
        if not self.client:
            return
        try:
            keys = list(self.client.scan_iter("search:*"))
            if keys:
                self.client.delete(*keys)
        except Exception:
            pass
