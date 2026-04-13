from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ───────────────────────────────────────────────────────────────────
    app_env: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:8081", "http://localhost:3000"]

    # ── LLM ───────────────────────────────────────────────────────────────────
    anthropic_api_key: str
    llm_model: str = "claude-sonnet-4-6"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 1024

    # ── PostgreSQL + pgvector ─────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://trinity:trinity@localhost:5432/trinity"
    database_sync_url: str = "postgresql+psycopg://trinity:trinity@localhost:5432/trinity"
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # ── Neo4j ─────────────────────────────────────────────────────────────────
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Auth ──────────────────────────────────────────────────────────────────
    jwt_secret_key: str = "changeme"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    # ── Encryption ────────────────────────────────────────────────────────────
    master_encryption_key: str = "changeme"

    # ── Memory ────────────────────────────────────────────────────────────────
    memory_top_k: int = 5
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # ── Safety ────────────────────────────────────────────────────────────────
    crisis_intensity_threshold: float = 0.7


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
