"use client";

import { useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import * as api from "@/lib/api";
import QueryTable, { Column } from "./QueryTable";

const DATASET_SIZES = [100, 1000, 5000, 10000];

function GrowthChart({
  title,
  data,
  dataKey,
  color,
}: {
  title: string;
  data: Array<Record<string, number>>;
  dataKey: string;
  color: string;
}) {
  return (
    <div className="rounded-lg border border-gray-200 p-4 dark:border-gray-800">
      <h3 className="mb-3 text-sm font-semibold">{title}</h3>
      <div className="h-56 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="documents"
              type="number"
              scale="log"
              domain={["dataMin", "dataMax"]}
              fontSize={12}
              tickFormatter={(v) => v.toLocaleString()}
            />
            <YAxis fontSize={12} width={48} />
            <Tooltip
              labelFormatter={(v) => `${Number(v).toLocaleString()} docs`}
            />
            <Line
              type="monotone"
              dataKey={dataKey}
              stroke={color}
              strokeWidth={2}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default function BenchmarkPanel({
  initialBenchmarks,
}: {
  initialBenchmarks: api.BenchmarkResult[];
}) {
  const [benchmarks, setBenchmarks] =
    useState<api.BenchmarkResult[]>(initialBenchmarks);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleRun() {
    setRunning(true);
    setError(null);
    try {
      await api.runBenchmark(DATASET_SIZES, 3);
      // Reload the full history so the charts show all runs, newest included.
      const { benchmarks: history } = await api.fetchBenchmarks();
      setBenchmarks(history);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Benchmark failed.");
    } finally {
      setRunning(false);
    }
  }

  // For growth charts, keep only the most recent run per dataset size so the
  // lines are monotonic in document_count rather than zig-zagging across runs.
  const latestBySize = new Map<number, api.BenchmarkResult>();
  for (const b of benchmarks) {
    const existing = latestBySize.get(b.document_count);
    if (!existing || b.created_at > existing.created_at) {
      latestBySize.set(b.document_count, b);
    }
  }
  const growth = Array.from(latestBySize.values())
    .sort((a, b) => a.document_count - b.document_count)
    .map((b) => ({
      documents: b.document_count,
      buildTimeMs: b.index_build_time_ms,
      avgLatencyMs: b.average_latency_ms,
      p95LatencyMs: b.p95_latency_ms,
      hitRatePct: Number((b.cache_hit_rate * 100).toFixed(1)),
    }));

  const columns: Column<api.BenchmarkResult>[] = [
    { header: "Dataset", render: (r) => r.dataset_name },
    { header: "Docs", align: "right", render: (r) => r.document_count.toLocaleString() },
    { header: "Terms", align: "right", render: (r) => r.unique_terms.toLocaleString() },
    { header: "Postings", align: "right", render: (r) => r.total_postings.toLocaleString() },
    { header: "Build (ms)", align: "right", render: (r) => r.index_build_time_ms.toFixed(1) },
    { header: "Avg (ms)", align: "right", render: (r) => r.average_latency_ms.toFixed(4) },
    { header: "p50", align: "right", render: (r) => r.p50_latency_ms.toFixed(4) },
    { header: "p95", align: "right", render: (r) => r.p95_latency_ms.toFixed(4) },
    { header: "p99", align: "right", render: (r) => r.p99_latency_ms.toFixed(4) },
    { header: "Hit rate", align: "right", render: (r) => `${(r.cache_hit_rate * 100).toFixed(0)}%` },
  ];

  return (
    <section className="mt-10">
      <div className="mb-3 flex items-center justify-between gap-4">
        <h2 className="text-lg font-semibold">Benchmarks</h2>
        <button
          onClick={handleRun}
          disabled={running}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {running ? "Running…" : "Run benchmark"}
        </button>
      </div>

      <p className="mb-4 rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-800 dark:bg-amber-950 dark:text-amber-300">
        Development benchmark using fake Redis. Rerun with real Redis before
        publishing final performance numbers.
      </p>

      {error && (
        <p className="mb-4 rounded-md bg-red-50 px-4 py-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
          {error}
        </p>
      )}

      <QueryTable
        title="Benchmark results (latency in ms)"
        columns={columns}
        rows={benchmarks}
        emptyText="No benchmarks yet. Click “Run benchmark” to generate results."
      />

      {growth.length > 0 && (
        <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
          <GrowthChart
            title="Documents vs index build time (ms)"
            data={growth}
            dataKey="buildTimeMs"
            color="#dc2626"
          />
          <GrowthChart
            title="Documents vs average latency (ms)"
            data={growth}
            dataKey="avgLatencyMs"
            color="#16a34a"
          />
          <GrowthChart
            title="Documents vs p95 latency (ms)"
            data={growth}
            dataKey="p95LatencyMs"
            color="#ea580c"
          />
          <GrowthChart
            title="Documents vs cache hit rate (%)"
            data={growth}
            dataKey="hitRatePct"
            color="#9333ea"
          />
        </div>
      )}
    </section>
  );
}
