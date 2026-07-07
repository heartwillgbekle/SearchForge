from fastapi import APIRouter, Depends, HTTPException, Query

from ..dependencies import get_engine

router = APIRouter()


@router.get("/search")
def search(
    q: str = Query(..., description="Search query"),
    top_k: int = Query(5, ge=1, le=50),
    ranking: str = Query("bm25", description="Ranking method: bm25 or tfidf"),
    engine=Depends(get_engine),
):
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query must not be empty")

    return engine.search(q, top_k=top_k, ranking=ranking)
