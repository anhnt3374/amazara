from pydantic import Field
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

    # Embeddings
    EMBEDDING_QWEN_ENABLED: bool = Field(default=True)
    EMBEDDING_QWEN_MODEL_ID: str = Field(default="Qwen/Qwen3-Embedding-0.6B")
    EMBEDDING_FG_CLIP_ENABLED: bool = Field(default=True)
    EMBEDDING_FG_CLIP_MODEL_ID: str = Field(default="qihoo360/fg-clip2-base")
    EMBEDDING_COLLECTION_PREFIX: str = Field(default="shope")
    EMBEDDING_MILVUS_URI: str = Field(default="http://localhost:19530")
    EMBEDDING_QUERY_TOP_K: int = Field(default=20)
    EMBEDDING_INDEX_ASYNC: bool = Field(default=True)
    EMBEDDING_BATCH_SIZE: int = Field(default=16)

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )


settings = Settings()
