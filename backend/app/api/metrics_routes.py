from fastapi import APIRouter, Depends, Query

from ..dependencies import get_engine

router = APIRouter()


@router.get("/metrics")
def metrics(engine=Depends(get_engine)):
    """Full metrics payload (kept for the original single-panel view)."""
    return engine.metrics()


@router.get("/metrics/overview")
def metrics_overview(engine=Depends(get_engine)):
    """Headline dashboard cards."""
    return engine.metrics_overview()


@router.get("/metrics/index")
def metrics_index(engine=Depends(get_engine)):
    """Index size and structure."""
    return engine.index_metrics()


@router.get("/metrics/search")
def metrics_search(engine=Depends(get_engine)):
    """Search behaviour: latency spread, result counts, zero-result count."""
    return engine.search_metrics()


@router.get("/metrics/cache")
def metrics_cache(engine=Depends(get_engine)):
    """Cache hit/miss statistics."""
    return engine.cache_metrics()


@router.get("/metrics/queries/popular")
def metrics_popular(
    top_k: int = Query(10, ge=1, le=50), engine=Depends(get_engine)
):
    return {"queries": engine.popular_queries(top_k)}


@router.get("/metrics/queries/slowest")
def metrics_slowest(
    top_k: int = Query(10, ge=1, le=50), engine=Depends(get_engine)
):
    return {"queries": engine.slowest_query_list(top_k)}


@router.get("/metrics/queries/recent")
def metrics_recent(
    top_k: int = Query(10, ge=1, le=50), engine=Depends(get_engine)
):
    return {"queries": engine.recent_queries(top_k)}


@router.get("/metrics/queries/zero-results")
def metrics_zero_results(
    top_k: int = Query(10, ge=1, le=50), engine=Depends(get_engine)
):
    return {"queries": engine.zero_result_queries(top_k)}


@router.get("/metrics/latency")
def metrics_latency(
    buckets: int = Query(30, ge=1, le=200), engine=Depends(get_engine)
):
    """Time series: searches, avg latency, and cache-hit rate per minute."""
    return {"series": engine.latency_over_time(buckets)}
