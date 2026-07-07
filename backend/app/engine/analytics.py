class Analytics:
    """Records search activity and summarizes performance.

    Backed by the Database layer so analytics survive program restarts.
    It stays independent of the searcher: the searcher produces results
    and latency, and this component only records and summarizes them.
    """

    def __init__(self, database):
        self.database = database

    def record_query(self, query, latency_ms, result_count):
        self.database.save_query(query, latency_ms, result_count)

    def total_searches(self):
        return self.database.total_searches()

    def average_latency(self):
        return self.database.average_latency()

    def popular_queries(self, top_k=5):
        return self.database.popular_queries(top_k)

    def slowest_queries(self, top_k=5):
        return self.database.slowest_queries(top_k)
