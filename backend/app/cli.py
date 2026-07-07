"""Interactive terminal search loop.

Kept for local exploration. It uses the same SearchEngine service the
API uses, so behavior stays in sync. Run with:

    python -m backend.app.cli
"""

from .service import SearchEngine


def print_stats(analytics):
    print("\nSearchForge Analytics")
    print("---------------------")
    print(f"Total searches: {analytics.total_searches()}")
    print(f"Average latency: {analytics.average_latency()} ms")

    popular = analytics.popular_queries()
    if popular:
        print("Most popular queries:")
        for i, (query, count) in enumerate(popular, start=1):
            print(f"{i}. {query} — {count}")
    print()


def print_slow(analytics):
    print("\nSlowest queries:")
    slowest = analytics.slowest_queries()
    if not slowest:
        print("No queries recorded yet.")
    for i, record in enumerate(slowest, start=1):
        print(f"{i}. {record['query_text']} — {record['latency_ms']} ms")
    print()


def main():
    engine = SearchEngine()
    inserted, skipped = engine.bootstrap()

    print("SearchForge Local Engine")
    print("------------------------")
    print(f"Documents indexed: {engine.index.total_documents()}")
    print(f"Unique terms: {engine.index.total_terms()}")
    print(f"Metadata: {inserted} new, {skipped} duplicate(s) skipped")
    print("Commands: stats, slow, exit")
    print()

    while True:
        query = input("Search query: ")
        command = query.lower().strip()

        if command in {"exit", "quit"}:
            print("Exiting SearchForge.")
            break

        if command == "stats":
            print_stats(engine.analytics)
            continue

        if command == "slow":
            print_slow(engine.analytics)
            continue

        response = engine.search(query)

        print(f"\nQuery latency: {response['latency_ms']} ms")
        print("Results:")

        if not response["results"]:
            print("No results found.")

        for i, result in enumerate(response["results"], start=1):
            print(f"\n{i}. {result['document']}")
            print(f"Score: {result['score']}")
            print(f"Snippet: {result['snippet']}")

        print()


if __name__ == "__main__":
    main()
