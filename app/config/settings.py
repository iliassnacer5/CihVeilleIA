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

    # API / Sécurité (exemples, à surcharger par variables d'env)
    api_secret_key: str = "7ec3505c04df465d6a2f3b9260655d78d49826d40026e632b732432ef1e6807f" # Example, should be env
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    allowed_origins: list[str] = ["*"]

    # MongoDB (stockage des documents enrichis)
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "VeillePlus"
    mongodb_collection_enriched: str = "enriched_documents"

    # Azure / Outlook (Optionnel)
    azure_client_id: Optional[str] = None
    azure_client_secret: Optional[str] = None
    azure_tenant_id: Optional[str] = None
    azure_sender_email: str = "veille-ia@cih.ma"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

