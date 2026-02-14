import secrets
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Paramètres globaux du projet de veille IA bancaire."""

    # Environnement
    env: str = "local"
    debug: bool = True

    # Chemins
    base_dir: Path = Path(__file__).resolve().parents[2]
    data_dir: Path = base_dir / "data"
    logs_dir: Path = base_dir / "logs"
    models_dir: Path = base_dir / "models"
    vector_store_dir: Path = base_dir / "vector_store"

    # API / Sécurité
    # Auto-generates a random key for local dev; MUST be overridden in production via .env
    api_secret_key: str = secrets.token_hex(32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    allowed_origins: list[str] = ["*"]

    # MongoDB (stockage des documents enrichis)
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "VeillePlus"
    mongodb_collection_enriched: str = "enriched_documents"

    # Redis (Cache & Task Queue)
    redis_url: str = "redis://localhost:6379/0"

    # Azure / Outlook
    azure_client_id: Optional[str] = None
    azure_client_secret: Optional[str] = None
    azure_tenant_id: Optional[str] = None
    azure_sender_email: str = "veille-ia@cih.ma"

    # SMTP Settings (Alternative)
    smtp_host: str = "smtp.office365.com"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True

    # Notification Logic
    notification_rag_threshold: float = 0.80
    notification_deduplication_window: int = 3600  # 1 hour
    notification_retry_attempts: int = 3

    # Rate Limiting
    rate_limit_per_minute: int = 60

    # LLM Providers (for RAG Generation)
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"

    @property
    def is_production(self) -> bool:
        return self.env.lower() == "production"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()

