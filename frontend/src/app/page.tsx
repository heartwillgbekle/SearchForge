"use client";

import { useCallback, useEffect, useState } from "react";
import * as api from "@/lib/api";
import SearchBar from "@/components/SearchBar";
import SearchResults from "@/components/SearchResults";
import MetricsPanel from "@/components/MetricsPanel";

export default function Home() {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState<api.SearchResponse | null>(null);
  const [metrics, setMetrics] = useState<api.Metrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadMetrics = useCallback(async () => {
    try {
      setMetrics(await api.fetchMetrics());
    } catch {
      // Metrics are secondary; don't block the search UI on them.
    }
  }, []);

  // Load metrics once on mount.
  useEffect(() => {
    loadMetrics();
  }, [loadMetrics]);

  async function runSearch(rawQuery: string) {
    const trimmed = rawQuery.trim();
    if (!trimmed) return;

    setLoading(true);
    setError(null);

    try {
      const result = await api.search(trimmed);
      setResponse(result);
      // Searching changes the stats, so refresh the metrics panel.
      loadMetrics();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setResponse(null);
    } finally {
      setLoading(false);
    }
  }

  function handleSearch() {
    runSearch(query);
  }

  // Clicking a suggestion fills the box and searches it immediately,
  // without waiting for the query state update to propagate.
  function handleSelectSuggestion(value: string) {
    setQuery(value);
    runSearch(value);
  }

  return (
    <main className="mx-auto w-full max-w-2xl px-4 py-12">
      <header className="mb-8">
        <h1 className="text-3xl font-bold">SearchForge</h1>
        <p className="mt-1 text-gray-600 dark:text-gray-400">
          Search documents using a custom inverted index and BM25 ranking.
        </p>
      </header>

      <SearchBar
        query={query}
        onQueryChange={setQuery}
        onSearch={handleSearch}
        onSelectSuggestion={handleSelectSuggestion}
        loading={loading}
      />

      {error && (
        <p className="mt-4 rounded-md bg-red-50 px-4 py-3 text-red-700 dark:bg-red-950 dark:text-red-300">
          {error}
        </p>
      )}

      {response && !error && <SearchResults response={response} />}

      <MetricsPanel metrics={metrics} />
    </main>
  );
}
