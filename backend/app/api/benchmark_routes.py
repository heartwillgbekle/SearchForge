"""Benchmark endpoints.

Benchmarks are separate from user search: POST /benchmarks/run builds
throwaway synthetic indexes, measures build time and query-latency
percentiles across dataset sizes, and persists each result. GET
/benchmarks returns the stored history for the dashboard.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..dependencies import get_engine

router = APIRouter()


class BenchmarkRequest(BaseModel):
    # Dataset sizes to sweep. Capped to keep a synchronous request bounded.
    sizes: Optional[List[int]] = Field(
        default=None,
        description="Document counts to benchmark; defaults to 100/1k/5k/10k.",
    )
    warm_passes: Optional[int] = Field(
        default=None,
        ge=0,
        le=10,
        description="Repeated passes over the workload to exercise caching.",
    )


# Guardrail so an accidental huge size can't hang the API worker.
MAX_DOCUMENT_COUNT = 20000


@router.post("/benchmarks/run")
def run_benchmark(
    body: BenchmarkRequest = BenchmarkRequest(), engine=Depends(get_engine)
):
    sizes = body.sizes
    if sizes:
        sizes = [n for n in sizes if 0 < n <= MAX_DOCUMENT_COUNT]
    results = engine.run_benchmark(sizes=sizes or None, warm_passes=body.warm_passes)
    return {"results": results}


@router.get("/benchmarks")
def benchmark_history(engine=Depends(get_engine)):
    return {"benchmarks": engine.benchmark_history()}
