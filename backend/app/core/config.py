from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("backend/.env", ".env"),
        extra="ignore",
    )

    # Database
    MYSQL_HOST: str = Field()
    MYSQL_PORT: int = Field()
    MYSQL_USER: str = Field()
    MYSQL_PASSWORD: str = Field()
    MYSQL_DATABASE: str = Field()

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
    SEMANTIC_FGCLIP_DIM: int = 512
    SEMANTIC_TEXT_DIM: int = 384
    SEMANTIC_HF_CACHE_DIR: str | None = None

    # ── Semantic search: indexing ──────────────────────────────────────────
    SEMANTIC_INDEX_BATCH_PRODUCTS: int = 64
    SEMANTIC_INDEX_BATCH_IMAGES: int = 32
    SEMANTIC_MAX_IMAGES_PER_PRODUCT: int = 4
    SEMANTIC_IMAGE_FETCH_TIMEOUT_SEC: int = 10
    SEMANTIC_IMAGE_FETCH_RETRIES: int = 2
    SEMANTIC_IMAGE_FETCH_CONCURRENCY: int = 16

    # ── Semantic search: Milvus ────────────────────────────────────────────
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    SEMANTIC_COLLECTION_IMAGE: str = "product_image_vec_v1"
    SEMANTIC_COLLECTION_TEXT: str = "product_desc_vec_v1"
    SEMANTIC_MILVUS_INDEX_TYPE: str = "IVF_FLAT"
    SEMANTIC_MILVUS_NLIST: int = 128
    SEMANTIC_MILVUS_NPROBE: int = 16

    # ── Semantic search: query ─────────────────────────────────────────────
    SEMANTIC_ANN_TOPN_IMAGE: int = 500
    SEMANTIC_ANN_TOPN_TEXT: int = 500
    SEMANTIC_IMAGE_AGG_TOP_K: int = 3
    SEMANTIC_FUSION_ALPHA: float = 0.5
    SEMANTIC_OUTLIER_RATIO_TAU: float = 0.6

    # ── Semantic search: cache ─────────────────────────────────────────────
    SEMANTIC_CACHE_BACKEND: Literal["memory", "redis"] = "memory"
    SEMANTIC_CACHE_TTL_SEC: int = 600
    SEMANTIC_CACHE_MAX_ENTRIES: int = 1024
    REDIS_URL: str = "redis://localhost:6379/0"

    @field_validator("SEMANTIC_FUSION_ALPHA", "SEMANTIC_OUTLIER_RATIO_TAU")
    @classmethod
    def _check_unit_interval(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("must be in [0.0, 1.0]")
        return v

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )


settings = Settings()
