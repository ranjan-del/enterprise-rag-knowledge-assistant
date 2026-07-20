"""Application configuration loaded from environment variables.

Uses pydantic-settings so values can come from the environment or a `.env`
file (see `.env.example`). Field names are matched case-insensitively, so the
environment variable ``DATABASE_URL`` populates the ``database_url`` field.

Design note: every default is chosen so the service runs offline with zero
setup. ``database_url`` defaults to a local SQLite file and the embedding /
answer stack is fully deterministic and in-process, so no API key, no Postgres,
and no vector-DB server are required to run or test the app.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings with offline-first defaults."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "enterprise-rag-knowledge-assistant"
    version: str = "1.0.0"

    # Database. Local default = SQLite (no install needed). Docker/hosting can
    # override with a PostgreSQL URL via the DATABASE_URL env var.
    database_url: str = "sqlite:///./rag.db"

    # Where uploaded files are stored on disk.
    upload_dir: str = "./data/uploads"

    # Embeddings (offline hashing embedder). Larger dim = finer buckets.
    embedding_dim: int = 512

    # Retrieval defaults.
    default_top_k: int = 5
    max_context_chars: int = 4000
    # Hybrid fusion weight: blend of semantic vs. lexical score (0..1).
    hybrid_alpha: float = 0.6

    # CORS: Angular dev-server origins allowed to call this API.
    cors_origins: str = "http://localhost:4200,http://localhost:80"

    # Auth (JWT). Override JWT_SECRET in production.
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    # Optional bootstrap admin, seeded on startup when both are set.
    first_admin_email: str | None = "admin@example.com"
    first_admin_password: str | None = "adminpass123"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()
