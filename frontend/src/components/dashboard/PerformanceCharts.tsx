"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { LatencyPoint } from "@/lib/api";

function ChartCard({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-gray-200 p-4 dark:border-gray-800">
      <h3 className="mb-3 text-sm font-semibold">{title}</h3>
      <div className="h-56 w-full">
        <ResponsiveContainer width="100%" height="100%">
          {children}
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// Show only the clock time (HH:MM) on the x-axis; the ISO bucket is minute-level.
function shortTime(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function PerformanceCharts({
  series,
}: {
  series: LatencyPoint[];
}) {
  if (series.length === 0) {
    return (
      <p className="rounded-lg border border-dashed border-gray-300 px-4 py-6 text-sm text-gray-400 dark:border-gray-700">
        Run some searches to populate the performance charts.
      </p>
    );
  }

  const data = series.map((point) => ({
    time: shortTime(point.bucket),
    searches: point.searches,
    latency: point.avg_latency_ms,
    hitRate: Number((point.cache_hit_rate * 100).toFixed(1)),
  }));

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <ChartCard title="Searches over time">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="time" fontSize={12} />
          <YAxis allowDecimals={false} fontSize={12} width={32} />
          <Tooltip />
          <Line
            type="monotone"
            dataKey="searches"
            stroke="#2563eb"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ChartCard>

      <ChartCard title="Average latency over time (ms)">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="time" fontSize={12} />
          <YAxis fontSize={12} width={40} />
          <Tooltip />
          <Line
            type="monotone"
            dataKey="latency"
            stroke="#16a34a"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ChartCard>

      <ChartCard title="Cache hit rate over time (%)">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="time" fontSize={12} />
          <YAxis domain={[0, 100]} fontSize={12} width={40} />
          <Tooltip />
          <Line
            type="monotone"
            dataKey="hitRate"
            stroke="#9333ea"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ChartCard>
    </div>
  );
}
