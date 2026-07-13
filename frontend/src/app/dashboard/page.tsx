"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import * as api from "@/lib/api";
import StatCard from "@/components/dashboard/StatCard";
import QueryTable, { Column } from "@/components/dashboard/QueryTable";
import PerformanceCharts from "@/components/dashboard/PerformanceCharts";
import BenchmarkPanel from "@/components/dashboard/BenchmarkPanel";

interface DashboardData {
  overview: api.OverviewMetrics;
  index: api.IndexMetrics;
  searchStats: api.SearchMetrics;
  cache: api.CacheMetrics;
  popular: api.CountedQuery[];
  slowest: api.SlowestQuery[];
  recent: api.RecentQuery[];
  zeroResults: api.CountedQuery[];
  latency: api.LatencyPoint[];
  benchmarks: api.BenchmarkResult[];
}

function pct(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [
        overview,
        index,
        searchStats,
        cache,
        popular,
        slowest,
        recent,
        zeroResults,
        latency,
        benchmarks,
      ] = await Promise.all([
        api.fetchOverview(),
        api.fetchIndexMetrics(),
        api.fetchSearchMetrics(),
        api.fetchCacheMetrics(),
        api.fetchPopularQueries(),
        api.fetchSlowestQueries(),
        api.fetchRecentQueries(),
        api.fetchZeroResultQueries(),
        api.fetchLatencySeries(),
        api.fetchBenchmarks(),
      ]);
      setData({
        overview,
        index,
        searchStats,
        cache,
        popular: popular.queries,
        slowest: slowest.queries,
        recent: recent.queries,
        zeroResults: zeroResults.queries,
        latency: latency.series,
        benchmarks: benchmarks.benchmarks,
      });
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load metrics.");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <main className="mx-auto w-full max-w-5xl px-4 py-12">
      <header className="mb-8 flex items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Performance Dashboard</h1>
          <p className="mt-1 text-gray-600 dark:text-gray-400">
            Index size, search latency, caching, and benchmarks.
          </p>
        </div>
        <Link
          href="/"
          className="shrink-0 rounded-md border border-gray-300 px-3 py-2 text-sm hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-900"
        >
          ← Search
        </Link>
      </header>

      {error && (
        <p className="mb-6 rounded-md bg-red-50 px-4 py-3 text-red-700 dark:bg-red-950 dark:text-red-300">
          {error}
        </p>
      )}

      {!data ? (
        <p className="text-gray-500">Loading metrics…</p>
      ) : (
        <>
          {/* Overview cards */}
          <section>
            <h2 className="mb-3 text-lg font-semibold">Overview</h2>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <StatCard
                label="Documents indexed"
                value={data.overview.documents_indexed.toLocaleString()}
              />
              <StatCard
                label="Unique terms"
                value={data.overview.unique_terms.toLocaleString()}
              />
              <StatCard
                label="Average latency"
                value={`${data.overview.average_latency_ms} ms`}
              />
              <StatCard
                label="Cache hit rate"
                value={pct(data.overview.cache_hit_rate)}
              />
            </div>
          </section>

          {/* Index metrics */}
          <section className="mt-8">
            <h2 className="mb-3 text-lg font-semibold">
              Index
              <span className="ml-2 text-sm font-normal text-gray-500">
                Ranking: {data.index.ranking_method}
              </span>
            </h2>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
              <StatCard
                label="Documents"
                value={data.index.documents_indexed.toLocaleString()}
              />
              <StatCard
                label="Unique terms"
                value={data.index.unique_terms.toLocaleString()}
              />
              <StatCard
                label="Total postings"
                value={data.index.total_postings.toLocaleString()}
              />
              <StatCard
                label="Avg doc length"
                value={data.index.average_document_length}
              />
              <StatCard
                label="Build time"
                value={`${data.index.index_build_time_ms} ms`}
              />
              <StatCard
                label="Last indexed"
                value={
                  data.index.last_indexed_at
                    ? new Date(
                        data.index.last_indexed_at,
                      ).toLocaleString()
                    : "—"
                }
              />
            </div>
          </section>

          {/* Search metrics */}
          <section className="mt-8">
            <h2 className="mb-3 text-lg font-semibold">Search</h2>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
              <StatCard
                label="Total searches"
                value={data.searchStats.total_searches.toLocaleString()}
              />
              <StatCard
                label="Average latency"
                value={`${data.searchStats.average_latency_ms} ms`}
              />
              <StatCard
                label="Fastest query"
                value={`${data.searchStats.fastest_latency_ms} ms`}
              />
              <StatCard
                label="Slowest query"
                value={`${data.searchStats.slowest_latency_ms} ms`}
              />
              <StatCard
                label="Avg result count"
                value={data.searchStats.average_result_count}
              />
              <StatCard
                label="Zero-result searches"
                value={data.searchStats.zero_result_searches.toLocaleString()}
              />
            </div>
          </section>

          {/* Cache metrics */}
          <section className="mt-8">
            <h2 className="mb-3 text-lg font-semibold">
              Cache
              {!data.cache.cache_enabled && (
                <span className="ml-2 text-sm font-normal text-gray-500">
                  (disabled)
                </span>
              )}
            </h2>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
              <StatCard label="Cache hits" value={data.cache.cache_hits} />
              <StatCard label="Cache misses" value={data.cache.cache_misses} />
              <StatCard
                label="Hit rate"
                value={pct(data.cache.cache_hit_rate)}
              />
              <StatCard
                label="Avg cached"
                value={`${data.cache.average_cached_latency_ms} ms`}
              />
              <StatCard
                label="Avg uncached"
                value={`${data.cache.average_uncached_latency_ms} ms`}
              />
            </div>
          </section>

          {/* Tables */}
          <section className="mt-8 grid grid-cols-1 gap-4 lg:grid-cols-2">
            <QueryTable
              title="Most popular queries"
              columns={popularColumns}
              rows={data.popular}
            />
            <QueryTable
              title="Slowest queries"
              columns={slowestColumns}
              rows={data.slowest}
            />
            <QueryTable
              title="Recent searches"
              columns={recentColumns}
              rows={data.recent}
            />
            <QueryTable
              title="Zero-result queries"
              columns={popularColumns}
              rows={data.zeroResults}
              emptyText="No zero-result queries — every search matched something."
            />
          </section>

          {/* Performance charts */}
          <section className="mt-8">
            <h2 className="mb-3 text-lg font-semibold">Performance over time</h2>
            <PerformanceCharts series={data.latency} />
          </section>

          {/* Benchmarks */}
          <BenchmarkPanel initialBenchmarks={data.benchmarks} />
        </>
      )}
    </main>
  );
}

const popularColumns: Column<api.CountedQuery>[] = [
  { header: "Query", render: (r) => r.query },
  { header: "Count", align: "right", render: (r) => r.count },
];

const slowestColumns: Column<api.SlowestQuery>[] = [
  { header: "Query", render: (r) => r.query },
  { header: "Results", align: "right", render: (r) => r.result_count },
  { header: "Latency (ms)", align: "right", render: (r) => r.latency_ms },
];

const recentColumns: Column<api.RecentQuery>[] = [
  { header: "Query", render: (r) => r.query },
  { header: "Results", align: "right", render: (r) => r.result_count },
  { header: "Latency (ms)", align: "right", render: (r) => r.latency_ms },
  {
    header: "Cache",
    render: (r) => (r.cache_hit ? "hit" : "miss"),
  },
];
