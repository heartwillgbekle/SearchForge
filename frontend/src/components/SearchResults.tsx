import { SearchResponse } from "@/lib/api";
import ResultCard from "./ResultCard";

export default function SearchResults({
  response,
}: {
  response: SearchResponse;
}) {
  return (
    <section className="mt-6">
      <p className="text-sm text-gray-500">
        {response.result_count}{" "}
        {response.result_count === 1 ? "result" : "results"} in{" "}
        {response.latency_ms} ms
      </p>

      {response.result_count === 0 ? (
        <p className="mt-4 text-gray-600 dark:text-gray-400">
          No results found for “{response.query}”.
        </p>
      ) : (
        <div className="mt-2">
          {response.results.map((result) => (
            <ResultCard key={result.document} result={result} />
          ))}
        </div>
      )}
    </section>
  );
}
