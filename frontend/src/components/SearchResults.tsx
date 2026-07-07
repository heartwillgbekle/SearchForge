import { SearchResponse } from "@/lib/api";
import ResultCard from "./ResultCard";

export default function SearchResults({
  response,
}: {
  response: SearchResponse;
}) {
  return (
    <section className="mt-6">
      <p className="flex items-center gap-2 text-sm text-gray-500">
        <span>
          {response.result_count}{" "}
          {response.result_count === 1 ? "result" : "results"} in{" "}
          {response.latency_ms} ms
        </span>
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${
            response.cache_hit
              ? "bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-300"
              : "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400"
          }`}
        >
          Cache: {response.cache_hit ? "hit" : "miss"}
        </span>
        <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700 dark:bg-blue-950 dark:text-blue-300">
          {response.ranking_method}
        </span>
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
