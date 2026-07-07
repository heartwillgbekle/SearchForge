class Analytics:
    """Records search activity and summarizes performance.

    Backed by a QueryRepository (PostgreSQL) so analytics survive restarts.
    It stays independent of the searcher: the searcher produces results and
    latency; this component only records and summarizes them.
    """

    def __init__(self, query_repository):
        self.queries = query_repository

    def record_query(
        self,
        query,
        normalized_query,
        latency_ms,
        result_count,
        cache_hit=False,
        ranking_method="BM25",
    ):
        self.queries.save(
            query_text=query,
            normalized_query=normalized_query,
            latency_ms=latency_ms,
            result_count=result_count,
            cache_hit=cache_hit,
            ranking_method=ranking_method,
        )

    def total_searches(self):
        return self.queries.total_searches()

    def average_latency(self):
        return self.queries.average_latency()

    def popular_queries(self, top_k=5):
        return self.queries.popular_queries(top_k)

    def slowest_queries(self, top_k=5):
        return self.queries.slowest_queries(top_k)

    # ---- cache performance ----------------------------------------------

    def cache_hits(self):
        return self.queries.cache_hits()

    def cache_misses(self):
        return self.queries.cache_misses()

    def cache_hit_rate(self):
        total = self.total_searches()
        if total == 0:
            return 0.0
        return round(self.cache_hits() / total, 3)

    def average_cached_latency(self):
        return self.queries.average_latency_by_cache(True)

    def average_uncached_latency(self):
        return self.queries.average_latency_by_cache(False)
