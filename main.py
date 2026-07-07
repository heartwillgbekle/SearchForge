from engine.analytics import Analytics
from engine.database import Database
from engine.document_loader import load_documents
from engine.indexer import InvertedIndex
from engine.searcher import Searcher


def total_postings(index):
    return sum(len(postings) for postings in index.index.values())


def save_documents_metadata(database, index):
    inserted = 0
    skipped = 0
    for file_name, text in index.documents.items():
        was_inserted = database.save_document(
            file_name=file_name,
            title=file_name.rsplit(".", 1)[0],
            file_path=f"documents/{file_name}",
            word_count=index.document_lengths.get(file_name, 0),
            text=text,
        )
        if was_inserted:
            inserted += 1
        else:
            skipped += 1
    return inserted, skipped


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
    documents = load_documents("documents")

    index = InvertedIndex()
    index.build(documents)

    searcher = Searcher(index)

    database = Database()
    analytics = Analytics(database)

    inserted, skipped = save_documents_metadata(database, index)
    database.save_index_metadata(
        total_documents=index.total_documents(),
        total_terms=index.total_terms(),
        total_postings=total_postings(index),
    )

    print("SearchForge Local Engine")
    print("------------------------")
    print(f"Documents indexed: {index.total_documents()}")
    print(f"Unique terms: {index.total_terms()}")
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
            print_stats(analytics)
            continue

        if command == "slow":
            print_slow(analytics)
            continue

        response = searcher.search(query)

        analytics.record_query(
            query=query,
            latency_ms=response["latency_ms"],
            result_count=len(response["results"]),
        )

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
