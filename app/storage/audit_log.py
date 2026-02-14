import logging
import asyncio
from datetime import datetime
from typing import Any, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings

from app.storage.audit_repository import AuditRepository

logger = logging.getLogger(__name__)

class AuditLogger:
    """Service de journalisation d'audit asynchrone pour la conformité bancaire."""

    def __init__(self, repository: Optional[AuditRepository] = None):
        self.repository = repository or AuditRepository()

    async def ensure_indexes(self):
        await self.repository.ensure_indexes()

    async def log_event(
        self, 
        module: str, 
        action: str, 
        status: str, 
        details: Dict[str, Any], 
        user_id: str = "system",
        entity: Optional[str] = None,
        entity_id: Optional[str] = None
    ):
        """Enregistre un événement d'audit de manière asynchrone."""
        
        entry = {
            "timestamp": datetime.utcnow().timestamp(),
            "module": module,
            "action": action,
            "status": status,
            "details": details,
            "user_id": user_id,
            "username": details.get("username", "system"),
            "role": details.get("role", "ROLE_USER"),
            "ip_address": details.get("ip_address", "0.0.0.0"),
            "entity": entity,
            "entity_id": entity_id
        }
        
        try:
            await self.repository.save_log(entry)
            logger.info(f"Audit: {module} | {action} | {status}")
        except Exception as e:
            logger.error(f"Échec de l'écriture du log d'audit: {e}")

# Instance globale pour compatibilité
audit_logger = AuditLogger()
