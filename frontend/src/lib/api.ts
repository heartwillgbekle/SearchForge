// Typed client for the SearchForge FastAPI backend.

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export interface SearchResult {
  document: string;
  score: number;
  snippet: string;
}

export interface SearchResponse {
  query: string;
  latency_ms: number;
  result_count: number;
  cache_hit: boolean;
  ranking_method: string;
  results: SearchResult[];
}

export interface PopularQuery {
  query: string;
  count: number;
}

export interface SlowQuery {
  query: string;
  latency_ms: number;
}

export interface Metrics {
  documents_indexed: number;
  unique_terms: number;
  total_postings: number;
  total_searches: number;
  average_latency_ms: number;
  average_document_length: number;
  ranking_method: string;
  cache_enabled: boolean;
  cache_hits: number;
  cache_misses: number;
  cache_hit_rate: number;
  average_cached_latency_ms: number;
  average_uncached_latency_ms: number;
  popular_queries: PopularQuery[];
  slowest_queries: SlowQuery[];
}

// Shared message so the UI can suggest the fix (start the backend).
const CONNECTION_ERROR =
  "Could not connect to SearchForge API. Make sure the backend is running.";

async function getJson<T>(path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`);
  } catch {
    // Network-level failure (backend down, CORS, DNS, etc.)
    throw new Error(CONNECTION_ERROR);
  }

  if (!response.ok) {
    // Try to surface FastAPI's {"detail": "..."} message.
    let detail = `Request failed with status ${response.status}`;
    try {
      const body = await response.json();
      if (body?.detail) detail = body.detail;
    } catch {
      // ignore non-JSON error bodies
    }
    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}

export function search(query: string): Promise<SearchResponse> {
  return getJson<SearchResponse>(`/search?q=${encodeURIComponent(query)}`);
}

export function fetchMetrics(): Promise<Metrics> {
  return getJson<Metrics>("/metrics");
}

export interface AutocompleteResponse {
  prefix: string;
  suggestions: string[];
}

export function autocomplete(prefix: string): Promise<AutocompleteResponse> {
  return getJson<AutocompleteResponse>(
    `/autocomplete?prefix=${encodeURIComponent(prefix)}`,
  );
}

// ---- dashboard metrics -----------------------------------------------------

export interface OverviewMetrics {
  documents_indexed: number;
  unique_terms: number;
  total_postings: number;
  average_document_length: number;
  index_build_time_ms: number;
  ranking_method: string;
  total_searches: number;
  average_latency_ms: number;
  cache_hit_rate: number;
}

export interface IndexMetrics {
  documents_indexed: number;
  unique_terms: number;
  total_postings: number;
  average_document_length: number;
  index_build_time_ms: number;
  ranking_method: string;
  last_indexed_at: string | null;
}

export interface SearchMetrics {
  total_searches: number;
  average_latency_ms: number;
  fastest_latency_ms: number;
  slowest_latency_ms: number;
  average_result_count: number;
  zero_result_searches: number;
}

export interface CacheMetrics {
  cache_enabled: boolean;
  cache_hits: number;
  cache_misses: number;
  cache_hit_rate: number;
  average_cached_latency_ms: number;
  average_uncached_latency_ms: number;
}

export interface RecentQuery {
  query: string;
  latency_ms: number;
  result_count: number;
  cache_hit: boolean;
  ranking_method: string;
  created_at: string;
}

export interface SlowestQuery {
  query: string;
  latency_ms: number;
  result_count: number;
}

export interface CountedQuery {
  query: string;
  count: number;
}

export interface LatencyPoint {
  bucket: string;
  searches: number;
  avg_latency_ms: number;
  cache_hit_rate: number;
}

export interface BenchmarkResult {
  id: number;
  dataset_name: string;
  document_count: number;
  unique_terms: number;
  total_postings: number;
  index_build_time_ms: number;
  average_latency_ms: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
  cache_hit_rate: number;
  notes: string | null;
  created_at: string;
  // Present on freshly-run results, absent on history rows.
  memory_peak_mb?: number;
  query_count?: number;
  cache_mode?: string;
  ranking_method?: string;
}

export function fetchOverview(): Promise<OverviewMetrics> {
  return getJson<OverviewMetrics>("/metrics/overview");
}

export function fetchIndexMetrics(): Promise<IndexMetrics> {
  return getJson<IndexMetrics>("/metrics/index");
}

export function fetchSearchMetrics(): Promise<SearchMetrics> {
  return getJson<SearchMetrics>("/metrics/search");
}

export function fetchCacheMetrics(): Promise<CacheMetrics> {
  return getJson<CacheMetrics>("/metrics/cache");
}

export function fetchPopularQueries(): Promise<{ queries: CountedQuery[] }> {
  return getJson<{ queries: CountedQuery[] }>("/metrics/queries/popular");
}

export function fetchSlowestQueries(): Promise<{ queries: SlowestQuery[] }> {
  return getJson<{ queries: SlowestQuery[] }>("/metrics/queries/slowest");
}

export function fetchRecentQueries(): Promise<{ queries: RecentQuery[] }> {
  return getJson<{ queries: RecentQuery[] }>("/metrics/queries/recent");
}

export function fetchZeroResultQueries(): Promise<{ queries: CountedQuery[] }> {
  return getJson<{ queries: CountedQuery[] }>(
    "/metrics/queries/zero-results",
  );
}

export function fetchLatencySeries(): Promise<{ series: LatencyPoint[] }> {
  return getJson<{ series: LatencyPoint[] }>("/metrics/latency");
}

export function fetchBenchmarks(): Promise<{ benchmarks: BenchmarkResult[] }> {
  return getJson<{ benchmarks: BenchmarkResult[] }>("/benchmarks");
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new Error(CONNECTION_ERROR);
  }

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const data = await response.json();
      if (data?.detail) detail = data.detail;
    } catch {
      // ignore non-JSON error bodies
    }
    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}

export function runBenchmark(
  sizes?: number[],
  warmPasses?: number,
): Promise<{ results: BenchmarkResult[] }> {
  return postJson<{ results: BenchmarkResult[] }>("/benchmarks/run", {
    sizes,
    warm_passes: warmPasses,
  });
}
