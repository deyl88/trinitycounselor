from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── App ──────────────────────────────────────────────────────────────────
    app_name: str = "Trinity Counselor"
    app_env: str = "development"
    debug: bool = False
    secret_key: str

    # ── Database (SQLAlchemy async) ───────────────────────────────────────────
    database_url: str  # postgresql+asyncpg://...

    # ── Database (psycopg3 — LangGraph checkpointer + PGVector) ─────────────
    postgres_url: str  # postgresql://...

    # ── Neo4j ────────────────────────────────────────────────────────────────
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str

    # ── Anthropic ────────────────────────────────────────────────────────────
    anthropic_api_key: str
    claude_model: str = "claude-sonnet-4-6"

    # ── OpenAI (embeddings) ───────────────────────────────────────────────────
    openai_api_key: str

    # ── JWT ──────────────────────────────────────────────────────────────────
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours

    # ── Encryption ────────────────────────────────────────────────────────────
    # base64-encoded 32-byte master key used to derive per-user encryption keys
    master_key: str


settings = Settings()  # type: ignore[call-arg]
