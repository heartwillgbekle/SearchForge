from engine.document_loader import load_documents
from engine.indexer import InvertedIndex
from engine.searcher import Searcher


def main():
    documents = load_documents("documents")

    index = InvertedIndex()
    index.build(documents)

    searcher = Searcher(index)

    print("SearchForge Local Engine")
    print("------------------------")
    print(f"Documents indexed: {index.total_documents()}")
    print(f"Unique terms: {index.total_terms()}")
    print()

    while True:
        query = input("Search query: ")

        if query.lower() in {"exit", "quit"}:
            print("Exiting SearchForge.")
            break

        response = searcher.search(query)

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
