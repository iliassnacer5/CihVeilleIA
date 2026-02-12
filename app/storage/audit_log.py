import logging
import asyncio
from datetime import datetime
from typing import Any, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings

logger = logging.getLogger(__name__)

class AuditLogger:
    """Service de journalisation d'audit asynchrone pour la conformité bancaire."""

    def __init__(self, db_name: str = "cih_audit"):
        self._uri = settings.mongodb_uri
        self._db_name = db_name
        self._client = None
        self._collection = None

    def _get_collection(self):
        if self._collection is None:
            self._client = AsyncIOMotorClient(self._uri)
            self._db = self._client[self._db_name]
            self._collection = self._db["audit_trail"]
        return self._collection

    async def ensure_indexes(self):
        col = self._get_collection()
        await col.create_index([("timestamp", -1)])
        await col.create_index([("event_type", 1)])

    async def log_event_async(
        self, 
        event_type: str, 
        action: str, 
        status: str, 
        details: Dict[str, Any], 
        user_id: str = "system"
    ):
        """Enregistre un événement d'audit de manière asynchrone."""
        col = self._get_collection()
        
        entry = {
            "timestamp": datetime.utcnow(),
            "event_type": event_type,
            "action": action,
            "status": status,
            "details": details,
            "user_id": user_id
        }
        
        try:
            await col.insert_one(entry)
            logger.info(f"Audit: {event_type} | {action} | {status}")
        except Exception as e:
            logger.error(f"Échec de l'écriture du log d'audit: {e}")

    def log_event(self, *args, **kwargs):
        """Wrapper synchrone (fire-and-forget) pour compatibilité."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.log_event_async(*args, **kwargs))
            else:
                asyncio.run(self.log_event_async(*args, **kwargs))
        except Exception:
            # Fallback if loop is missing or other issues
            import threading
            threading.Thread(target=lambda: asyncio.run(self.log_event_async(*args, **kwargs))).start()

# Instance globale
audit_logger = AuditLogger()
