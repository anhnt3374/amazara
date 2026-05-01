import asyncio
import logging
import time
from contextlib import asynccontextmanager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

import app.db.base  # noqa: F401, E402 — registers all ORM models before first DB access
from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.api.v1.router import api_router  # noqa: E402
from app.core.config import settings  # noqa: E402

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Preload everything that has a non-trivial cold-start so the first
    # /search request doesn't pay for it: ML weights, Weaviate gRPC channel,
    # Postgres pool, Redis connection. Each step is independent — run in
    # parallel and tolerate failures (we still want the server to come up
    # even if e.g. Redis is down).
    from sqlalchemy import text
    from app.db.session import engine
    from app.services.search import vector_store
    from app.services.search.embedders.bge import BgeTextEmbedder
    from app.services.search.embedders.fgclip import FgClipEmbedder
    from app.services.search.search_service import _get_cache, aclose_cache

    logger.info("Lifespan startup: preloading models + opening connections…")
    started = time.perf_counter()

    async def _load_embedders():
        return await asyncio.gather(
            asyncio.to_thread(BgeTextEmbedder.get),
            asyncio.to_thread(FgClipEmbedder.get),
        )

    async def _ping_postgres():
        def _ping():
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        t0 = time.perf_counter()
        await asyncio.to_thread(_ping)
        return (time.perf_counter() - t0) * 1000

    async def _connect_weaviate():
        t0 = time.perf_counter()
        # connect() opens gRPC + REST; apply_runtime_hnsw_config() pushes
        # ef / dynamic_ef_* tunables to existing collections (no reindex).
        def _do():
            vector_store.connect()
            vector_store.apply_runtime_hnsw_config()
        await asyncio.to_thread(_do)
        return (time.perf_counter() - t0) * 1000

    async def _ping_redis():
        # Public-API ping: triggers RedisCache._conn() (binds aioredis to
        # the current loop) plus a real TCP roundtrip. A missing key is
        # fine; the existing get() path swallows connection errors so a
        # down Redis won't break startup, only log a warning.
        t0 = time.perf_counter()
        await _get_cache().get("__startup_ping__")
        return (time.perf_counter() - t0) * 1000

    embed_result, pg_ms, weav_ms, redis_ms = await asyncio.gather(
        _load_embedders(),
        _ping_postgres(),
        _connect_weaviate(),
        _ping_redis(),
        return_exceptions=True,
    )

    # Warm embedders on THIS thread (event loop thread). semantic_search
    # calls .encode() synchronously from here, so cuDNN kernel compile +
    # per-thread CUDA context init must happen here — not in the worker
    # thread that loaded the weights.
    if isinstance(embed_result, BaseException):
        logger.error("Embedder load failed: %s", embed_result)
    else:
        bge, fg = embed_result
        try:
            warm_t0 = time.perf_counter()
            bge.encode(["warmup"])
            fg.encode(["warmup"])
            warm_ms = (time.perf_counter() - warm_t0) * 1000
            logger.info(
                "Embedders ready: bge=%s fgclip=%s warm=%.0fms",
                next(bge._model.parameters()).device,
                next(fg._model.parameters()).device,
                warm_ms,
            )
        except Exception:
            logger.exception("Embedder warmup failed")

    def _report(name: str, result):
        if isinstance(result, BaseException):
            logger.warning("%s preconnect failed: %s", name, result)
        else:
            logger.info("%s ready in %.0fms", name, result)

    _report("Postgres", pg_ms)
    _report("Weaviate", weav_ms)
    _report("Redis", redis_ms)
    logger.info("Lifespan startup total=%.2fs", time.perf_counter() - started)

    try:
        yield
    finally:
        try:
            await aclose_cache()
        except Exception:
            logger.exception("aclose_cache failed")
        try:
            vector_store.disconnect()
        except Exception:
            logger.exception("vector_store.disconnect failed")
        try:
            engine.dispose()
        except Exception:
            logger.exception("engine.dispose failed")


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
