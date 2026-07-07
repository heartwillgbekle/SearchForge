from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import document_routes, metrics_routes, search_routes
from .dependencies import set_engine
from .service import SearchEngine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Build the index and connect storage once, at startup.
    engine = SearchEngine()
    inserted, skipped = engine.bootstrap()
    set_engine(engine)
    print(
        f"SearchForge API ready: {engine.index.total_documents()} documents, "
        f"{engine.index.total_terms()} terms "
        f"({inserted} new, {skipped} duplicate(s) skipped)"
    )
    yield


app = FastAPI(title="SearchForge API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to the frontend origin before deploy
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_routes.router)
app.include_router(metrics_routes.router)
app.include_router(document_routes.router)


@app.get("/")
def root():
    return {"message": "SearchForge API is running"}
