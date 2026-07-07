from collections import Counter
from datetime import datetime


class Analytics:
    """Records search activity in memory and summarizes performance.

    This is deliberately independent of the searcher. Later it can be
    backed by a database (PostgreSQL) without touching search logic.
    """

    def __init__(self):
        self.queries = []

    def record_query(self, query, latency_ms, result_count):
        self.queries.append({
            "query": query,
            "latency_ms": latency_ms,
            "result_count": result_count,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        })

    def total_searches(self):
        return len(self.queries)

    def average_latency(self):
        if not self.queries:
            return 0.0

        total = sum(record["latency_ms"] for record in self.queries)
        return round(total / len(self.queries), 3)

    def popular_queries(self, top_k=5):
        counts = Counter(record["query"] for record in self.queries)
        return counts.most_common(top_k)

    def slowest_queries(self, top_k=5):
        ranked = sorted(
            self.queries,
            key=lambda record: record["latency_ms"],
            reverse=True,
        )
        return ranked[:top_k]
