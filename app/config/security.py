from pydantic_settings import BaseSettings
from typing import List

from urllib.parse import urlparse
from app.scraping.sources_registry import SOURCES_REGISTRY

class SecuritySettings(BaseSettings):
    """Paramètres de sécurité et conformité pour la veille bancaire."""

    # Whitelist des domaines autorisés (Auditabilité)
    # On la génère dynamiquement à partir du registre des sources
    SOURCE_WHITELIST: List[str] = list(set([
        urlparse(s["base_url"]).netloc for s in SOURCES_REGISTRY.values()
    ]))

    # Éthique et Conformité Scraping
    # Délai entre deux requêtes sur le même domaine (secondes)
    SCRAPING_MIN_DELAY: float = 2.0
    
    # Identité du bot pour la transparence
    USER_AGENT: str = "CIH-Veille-IA-Audit-Bot/1.0 (Contact: rssi@cihbank.ma; Bot de veille reglementaire PFE)"

    # Rétention des logs d'audit (jours)
    AUDIT_RETENTION_DAYS: int = 90

    class Config:
        env_prefix = "SEC_"
        case_sensitive = True

security_settings = SecuritySettings()
