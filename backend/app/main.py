import asyncio
import logging
import time
from contextlib import asynccontextmanager

import app.db.base  # noqa: F401 — registers all ORM models before first DB access
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm the semantic-search embedders so the first /search request doesn't
    # pay a multi-second cold-start. Both classes are singletons guarded by a
    # threading.Lock, so subsequent .get() calls are free.
    from app.services.search.embedders.bge import BgeTextEmbedder
    from app.services.search.embedders.fgclip import FgClipEmbedder

    logger.info("Preloading semantic-search embedders…")
    started = time.perf_counter()
    try:
        await asyncio.gather(
            asyncio.to_thread(BgeTextEmbedder.get),
            asyncio.to_thread(FgClipEmbedder.get),
        )
        elapsed = time.perf_counter() - started
        logger.info("Embedders ready in %.2fs", elapsed)
    except Exception:
        logger.exception("Failed to preload embedders; will fall back to lazy load")

    yield


app = FastAPI(
    title="Amaraza API",
    version="0.1.0",
    docs_url="/docs" if settings.APP_ENV == "development" else None,
    redoc_url="/redoc" if settings.APP_ENV == "development" else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
