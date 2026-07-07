from fastapi import APIRouter, Depends

from ..dependencies import get_engine

router = APIRouter()


@router.get("/metrics")
def metrics(engine=Depends(get_engine)):
    return engine.metrics()
