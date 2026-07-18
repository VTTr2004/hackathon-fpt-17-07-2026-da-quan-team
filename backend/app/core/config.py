from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Startup Due Diligence API"
    api_v1_prefix: str = "/api/v1"
    environment: str = "development"
    database_url: str = "postgresql+asyncpg://app:app@localhost:5432/startup_due_diligence"
    auto_create_tables: bool = True
    cors_origins: str = "http://localhost:3000"
    upload_dir: str = "./uploads"
    max_upload_mb: int = 25
    auth_secret: str = "change-this-secret-before-production"
    auth_token_ttl_hours: int = 24
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-flash-latest"
    gemini_ocr_model: str = "gemini-3.1-flash-lite"
    gemini_embed_model: str = "gemini-embedding-001"
    gemini_embed_dim: int = 1024
    gemini_timeout_seconds: float = 60
    goong_api_key: str | None = None
    google_geocoding_api_key: str | None = None
    google_places_api_key: str | None = None

    # LLM provider for RAG chat: "gemini" (default) or "nvidia" (GPT-OSS-120B).
    llm_provider: str = "gemini"
    nvidia_api_key: str | None = None
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_chat_model: str = "openai/gpt-oss-120b"
    nvidia_embed_model: str = "nvidia/nv-embedqa-e5-v5"
    nvidia_timeout_seconds: float = 60

    @model_validator(mode="after")
    def validate_production_auth_secret(self) -> "Settings":
        placeholders = {"", "change-this-secret-before-production", "replace-with-a-long-random-secret"}
        if self.environment.lower() in {"production", "prod"} and (
            self.auth_secret in placeholders or len(self.auth_secret) < 32
        ):
            raise ValueError("AUTH_SECRET must be a unique value of at least 32 characters in production")
        return self

    # RAG retrieval knobs (validated by the retrieval eval, see docs/methodology.md).
    rag_top_k: int = 5
    rag_candidate_k: int = 10
    rag_use_rerank: bool = False

    @property
    def gemini_api_keys(self) -> list[str]:
        """Return configured Gemini keys in failover order.

        GEMINI_API_KEY remains a string so existing single-key deployments keep
        working. Comma-separated values enable key rotation.
        """
        if not self.gemini_api_key:
            return []
        return list(dict.fromkeys(key.strip() for key in self.gemini_api_key.split(",") if key.strip()))

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
