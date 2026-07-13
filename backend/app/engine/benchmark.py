"""Benchmark runner for SearchForge.

This is deliberately separate from normal user search. It builds its own
synthetic corpus and its own in-memory index/searcher/cache so a benchmark
never pollutes the live index or the query analytics table. For each dataset
size it measures:

  - index build time
  - per-query latency (cold pass = cache misses, warm passes = cache hits)
  - latency percentiles (p50 / p95 / p99)
  - cache hit rate

The corpus and query workload are generated from a fixed seed so runs are
reproducible.

NOTE ON CACHING: the benchmark uses a small in-process dict cache that mirrors
the engine's get/set-by-normalized-query semantics. It intentionally does NOT
reuse the shared Redis/fakeredis SearchCache, so benchmark traffic never evicts
or overwrites live cached queries. The `notes` field records which Redis mode
the deployment is in, per the "label fake-Redis numbers as development" rule.
"""

import math
import random
import time
import tracemalloc

from .. import config
from .cache import normalize_query
from .indexer import InvertedIndex
from .ranker import DEFAULT_RANKING, get_ranker
from .searcher import Searcher

# Dataset sizes to sweep when no explicit sizes are requested.
DEFAULT_SIZES = [100, 1000, 5000, 10000]

# How many warm (repeated) passes over the query workload follow the single
# cold pass. With R warm passes the cache hit rate is R / (R + 1).
DEFAULT_WARM_PASSES = 3

# Vocabulary size for the synthetic corpus. A Zipf-like sampling weight gives a
# realistic spread of common vs. rare terms (so IDF actually varies).
VOCAB_SIZE = 800
DOC_MIN_WORDS = 20
DOC_MAX_WORDS = 120
SEED = 1234


def percentile(values, p):
    """Linear-interpolation percentile (like numpy's default)."""
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * (p / 100.0)
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return ordered[int(rank)]
    return ordered[low] + (ordered[high] - ordered[low]) * (rank - low)


def _vocabulary(size):
    # Pure-alphabetic tokens: the tokenizer keeps only \b[a-z]+\b, so any
    # digits would be dropped and the index would come out empty.
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    words = []
    i = 0
    while len(words) < size:
        n = i
        # Bijective base-26 -> a, b, ..., z, aa, ab, ...
        chars = []
        while True:
            chars.append(alphabet[n % 26])
            n = n // 26 - 1
            if n < 0:
                break
        word = "word" + "".join(reversed(chars))
        words.append(word)
        i += 1
    return words


def _sample_weights(size):
    # Zipf-ish: term i is weighted 1/(i+1), so low-index terms are common.
    return [1.0 / (i + 1) for i in range(size)]


def build_corpus(document_count, seed=SEED):
    """Generate a deterministic synthetic corpus: {doc_id: text}."""
    rng = random.Random(seed)
    vocab = _vocabulary(VOCAB_SIZE)
    weights = _sample_weights(VOCAB_SIZE)

    documents = {}
    for doc_index in range(document_count):
        length = rng.randint(DOC_MIN_WORDS, DOC_MAX_WORDS)
        words = rng.choices(vocab, weights=weights, k=length)
        documents[f"doc{doc_index:06d}.txt"] = " ".join(words)
    return documents


def build_workload(query_count=20, seed=SEED):
    """A fixed set of test queries drawn from the same vocabulary.

    Mixes common terms, rarer terms, and two-term queries so the workload
    exercises different posting-list sizes. A couple of out-of-vocabulary
    queries are appended to produce zero-result searches.
    """
    rng = random.Random(seed + 1)
    vocab = _vocabulary(VOCAB_SIZE)
    weights = _sample_weights(VOCAB_SIZE)

    queries = []
    for _ in range(query_count):
        if rng.random() < 0.4:
            terms = rng.choices(vocab, weights=weights, k=2)
        else:
            terms = rng.choices(vocab, weights=weights, k=1)
        queries.append(" ".join(terms))

    # Guaranteed misses (terms that never appear in the corpus vocabulary).
    queries.append("zzznotarealterm")
    queries.append("missingtoken anothermissing")
    return queries


def _total_postings(index):
    return sum(len(postings) for postings in index.index.values())


def run_single(
    document_count,
    dataset_name=None,
    warm_passes=DEFAULT_WARM_PASSES,
    top_k=5,
    ranking=None,
    seed=SEED,
):
    """Benchmark one dataset size and return a result dict.

    The returned dict is a superset of the `benchmarks` table columns; extra
    fields (memory_peak_mb, query_count, cache_mode) are for display only.
    """
    ranker = get_ranker(ranking)
    ranking_key = ranker.name.lower()
    name = dataset_name or f"synthetic-{document_count}"

    corpus = build_corpus(document_count, seed=seed)
    workload = build_workload(seed=seed)

    # 1. Index build (timed, with peak-memory sampling).
    index = InvertedIndex()
    tracemalloc.start()
    build_start = time.perf_counter()
    index.build(corpus)
    build_time_ms = (time.perf_counter() - build_start) * 1000
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    searcher = Searcher(index)

    # 2. Query workload. A dict cache mirrors the engine's normalized-query
    #    caching so warm passes are genuine hits. Cold pass = all misses.
    cache = {}
    latencies = []
    cache_hits = 0
    total_searches = 0
    total_passes = 1 + max(0, warm_passes)

    for pass_index in range(total_passes):
        for query in workload:
            key = f"{ranking_key}:{normalize_query(query)}"
            start = time.perf_counter()
            hit = key in cache
            if hit:
                _ = cache[key]  # serve from cache
            else:
                response = searcher.search(query, top_k=top_k, ranking=ranking)
                cache[key] = response
            latency_ms = (time.perf_counter() - start) * 1000

            latencies.append(latency_ms)
            total_searches += 1
            if hit:
                cache_hits += 1

    average_latency = sum(latencies) / len(latencies) if latencies else 0.0
    cache_hit_rate = cache_hits / total_searches if total_searches else 0.0

    redis_mode = "fake-redis" if config.USE_FAKE_REDIS else "redis"
    notes = (
        f"Development benchmark (isolated dict cache; deployment Redis mode: "
        f"{redis_mode}). Seed {seed}, {warm_passes} warm pass(es)."
    )

    return {
        "dataset_name": name,
        "document_count": document_count,
        "unique_terms": index.total_terms(),
        "total_postings": _total_postings(index),
        "index_build_time_ms": round(build_time_ms, 3),
        "average_latency_ms": round(average_latency, 4),
        "p50_latency_ms": round(percentile(latencies, 50), 4),
        "p95_latency_ms": round(percentile(latencies, 95), 4),
        "p99_latency_ms": round(percentile(latencies, 99), 4),
        "cache_hit_rate": round(cache_hit_rate, 4),
        "notes": notes,
        # Display-only extras (not persisted to the benchmarks table).
        "memory_peak_mb": round(peak_bytes / (1024 * 1024), 2),
        "query_count": len(workload),
        "cache_mode": redis_mode,
        "ranking_method": ranker.name,
    }


def run_benchmark(
    sizes=None,
    warm_passes=DEFAULT_WARM_PASSES,
    ranking=None,
    seed=SEED,
    repository=None,
):
    """Run the benchmark across several dataset sizes.

    If a BenchmarkRepository is provided, each result is persisted and the
    stored row (with id/created_at) is returned; otherwise the in-memory
    result dicts are returned.
    """
    sizes = sizes or DEFAULT_SIZES
    results = []
    for size in sizes:
        result = run_single(
            size, warm_passes=warm_passes, ranking=ranking, seed=seed
        )
        if repository is not None:
            stored = repository.save(result)
            # Keep the display-only extras the DB row doesn't carry.
            for extra in ("memory_peak_mb", "query_count", "cache_mode",
                          "ranking_method"):
                stored[extra] = result[extra]
            results.append(stored)
        else:
            results.append(result)
    return results
