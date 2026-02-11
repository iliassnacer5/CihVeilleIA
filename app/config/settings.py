from pathlib import Path
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
    api_secret_key: str = "change-me-in-prod"
    allowed_origins: list[str] = ["*"]

    # MongoDB (stockage des documents enrichis)
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "VeillePlus"
    mongodb_collection_enriched: str = "enriched_documents"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

