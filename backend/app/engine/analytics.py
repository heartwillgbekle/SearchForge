class Analytics:
    """Records search activity and summarizes performance.

    Backed by the Database layer so analytics survive program restarts.
    It stays independent of the searcher: the searcher produces results
    and latency, and this component only records and summarizes them.
    """

    def __init__(self, database):
        self.database = database

    def record_query(self, query, latency_ms, result_count, cache_hit=False):
        self.database.save_query(query, latency_ms, result_count, cache_hit)

    def total_searches(self):
        return self.database.total_searches()

    def average_latency(self):
        return self.database.average_latency()

    def popular_queries(self, top_k=5):
        return self.database.popular_queries(top_k)

    def slowest_queries(self, top_k=5):
        return self.database.slowest_queries(top_k)

    # ---- cache performance ----------------------------------------------

    def cache_hits(self):
        return self.database.cache_hits()

    def cache_misses(self):
        return self.database.cache_misses()

    def cache_hit_rate(self):
        total = self.total_searches()
        if total == 0:
            return 0.0
        return round(self.cache_hits() / total, 3)

    def average_cached_latency(self):
        return self.database.average_latency_by_cache(True)

    def average_uncached_latency(self):
        return self.database.average_latency_by_cache(False)
