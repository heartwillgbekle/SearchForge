from fastapi import APIRouter, Depends, Query

from ..dependencies import get_engine

router = APIRouter()


@router.get("/autocomplete")
def autocomplete(
    prefix: str = Query("", description="Prefix to complete"),
    limit: int = Query(5, ge=1, le=20),
    engine=Depends(get_engine),
):
    suggestions = engine.suggest(prefix, limit=limit) if prefix.strip() else []
    return {"prefix": prefix, "suggestions": suggestions}
