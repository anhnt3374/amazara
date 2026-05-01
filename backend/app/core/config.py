from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("backend/.env", ".env"),
        extra="ignore",
    )

    # Database
    POSTGRES_HOST: str = Field()
    POSTGRES_PORT: int = Field()
    POSTGRES_USER: str = Field()
    POSTGRES_PASSWORD: str = Field()
    POSTGRES_DATABASE: str = Field()

    # JWT
    SECRET_KEY: str = Field()
    ALGORITHM: str = Field()
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field()

    # App
    APP_ENV: str = Field()

    # Chat
    BOT_ENGINE: str = Field()
    GROQ_API_KEY: str = Field()
    GROQ_MODEL: str = Field()
    GROQ_BASE_URL: str = Field()
    LANGSMITH_TRACING: bool = Field()
    LANGSMITH_API_KEY: str = Field()
    LANGSMITH_PROJECT: str = Field()

    # ── Semantic search: models ────────────────────────────────────────────
    SEMANTIC_FGCLIP_MODEL: str = "qihoo360/fg-clip2-base"
    SEMANTIC_TEXT_MODEL: str = "BAAI/bge-small-en-v1.5"
    SEMANTIC_DEVICE: Literal["auto", "cuda", "cpu"] = "auto"
    SEMANTIC_FGCLIP_DIM: int = 768
    SEMANTIC_TEXT_DIM: int = 384
    SEMANTIC_HF_CACHE_DIR: str | None = None

    # ── Semantic search: indexing ──────────────────────────────────────────
    SEMANTIC_INDEX_BATCH_PRODUCTS: int = 64
    SEMANTIC_INDEX_BATCH_IMAGES: int = 32
    SEMANTIC_MAX_IMAGES_PER_PRODUCT: int = 4
    SEMANTIC_IMAGE_FETCH_TIMEOUT_SEC: int = 10
    SEMANTIC_IMAGE_FETCH_RETRIES: int = 2
    SEMANTIC_IMAGE_FETCH_CONCURRENCY: int = 16

    # ── Semantic search: Weaviate Cloud ────────────────────────────────────
    WEAVIATE_URL: str = Field()
    WEAVIATE_API_KEY: str = Field()
    SEMANTIC_COLLECTION_IMAGE: str = "ProductImageVecV1"
    SEMANTIC_COLLECTION_TEXT: str = "ProductDescVecV1"

    # ── Semantic search: query ─────────────────────────────────────────────
    SEMANTIC_ANN_TOPN_IMAGE: int = 500
    SEMANTIC_ANN_TOPN_TEXT: int = 500
    SEMANTIC_IMAGE_AGG_TOP_K: int = 3
    SEMANTIC_FUSION_ALPHA: float = 0.8
    SEMANTIC_OUTLIER_RATIO_TAU: float = 0.6

    # ── Semantic search: HNSW tuning ───────────────────────────────────────
    # ef = search beam width. None → use Weaviate's dynamic ef (capped at
    # dynamic_ef_max). Static value gives consistent latency/recall trade
    # regardless of top_k.
    SEMANTIC_HNSW_EF: int | None = None
    SEMANTIC_HNSW_DYNAMIC_EF_FACTOR: int = 8
    SEMANTIC_HNSW_DYNAMIC_EF_MIN: int = 100
    SEMANTIC_HNSW_DYNAMIC_EF_MAX: int = 500

    # ── Semantic search: cache (Redis Cloud) ───────────────────────────────
    SEMANTIC_CACHE_BACKEND: Literal["memory", "redis"] = "redis"
    SEMANTIC_CACHE_TTL_SEC: int = 600
    SEMANTIC_CACHE_MAX_ENTRIES: int = 1024
    REDIS_URL: str = Field()

    @field_validator("SEMANTIC_FUSION_ALPHA", "SEMANTIC_OUTLIER_RATIO_TAU")
    @classmethod
    def _check_unit_interval(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("must be in [0.0, 1.0]")
        return v

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DATABASE}"
            f"?sslmode=require"
        )


settings = Settings()
