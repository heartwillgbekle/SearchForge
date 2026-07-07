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
