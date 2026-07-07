import { Metrics } from "@/lib/api";

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-gray-200 p-4 dark:border-gray-800">
      <div className="text-2xl font-semibold">{value}</div>
      <div className="mt-1 text-sm text-gray-500">{label}</div>
    </div>
  );
}

export default function MetricsPanel({ metrics }: { metrics: Metrics | null }) {
  if (!metrics) return null;

  return (
    <section className="mt-10">
      <h2 className="mb-3 text-lg font-semibold">Index & search metrics</h2>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Documents indexed" value={metrics.documents_indexed} />
        <Stat label="Unique terms" value={metrics.unique_terms} />
        <Stat label="Total searches" value={metrics.total_searches} />
        <Stat
          label="Average latency"
          value={`${metrics.average_latency_ms} ms`}
        />
      </div>
    </section>
  );
}
