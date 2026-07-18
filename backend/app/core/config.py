"""Application configuration loaded from environment variables.

Uses pydantic-settings so values can come from `.env` (see `.env.example`).
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings. TODO: fill in real defaults / validation."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "enterprise-rag-knowledge-assistant"
    version: str = "0.1.0"

    # Database (PostgreSQL) — see MEMORY.md Hosting (Neon/Supabase).
    database_url: str = "postgresql+psycopg2://postgres:postgres@db:5432/rag"

    # Vector DB (Qdrant) — see MEMORY.md Hosting (Qdrant Cloud / pgvector).
    qdrant_url: str = "http://qdrant:6333"
    qdrant_collection: str = "documents"

    # Embeddings + LLM. TODO: wire real providers/keys.
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    llm_provider: str = "openai"  # TODO: choose provider
    llm_api_key: str = ""

    # Auth. TODO: replace with a securely generated secret.
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
