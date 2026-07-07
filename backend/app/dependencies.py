"""Shared access to the single SearchEngine instance.

main.py builds the engine at startup and stores it here so route
modules can retrieve it without creating their own copies.
"""

from typing import Optional

from fastapi import HTTPException

from .service import SearchEngine

_engine: Optional[SearchEngine] = None


def set_engine(engine):
    global _engine
    _engine = engine


def get_engine():
    if _engine is None:
        raise HTTPException(status_code=503, detail="Search engine not ready")
    return _engine
