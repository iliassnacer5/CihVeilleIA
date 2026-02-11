import logging
from datetime import datetime
from typing import Any, Dict, Optional
from pymongo import MongoClient
from app.config.settings import settings

logger = logging.getLogger(__name__)

class AuditLogger:
    """Service de journalisation d'audit pour la conformité bancaire.
    
    Enregistre les événements critiques dans une collection MongoDB dédiée
    pour permettre un audit a posteriori (traçabilité complète).
    """

    def __init__(self, db_name: str = "cih_audit"):
        try:
            self._client = MongoClient(settings.mongodb_uri)
            self._db = self._client[db_name]
            self._collection = self._db["audit_trail"]
            # Indexation pour la performance de l'audit
            self._collection.create_index([("timestamp", -1)])
            self._collection.create_index([("event_type", 1)])
        except Exception as e:
            logger.error(f"Erreur d'initialisation de l'audit store: {e}")
            self._collection = None

    def log_event(
        self, 
        event_type: str, 
        action: str, 
        status: str, 
        details: Dict[str, Any], 
        user_id: str = "system"
    ):
        """Enregistre un événement d'audit.
        
        Types d'événements suggérés: 'SCRAPING', 'AI_REQUEST', 'SECURITY_ALERT'.
        """
        if self._collection is None:
            logger.warning(f"Audit log impossible (store non initialisé): {event_type} - {action}")
            return

        entry = {
            "timestamp": datetime.utcnow(),
            "event_type": event_type,
            "action": action,
            "status": status,
            "details": details,
            "user_id": user_id
        }
        
        try:
            self._collection.insert_one(entry)
            logger.info(f"Audit: {event_type} | {action} | {status}")
        except Exception as e:
            logger.error(f"Échec de l'écriture du log d'audit: {e}")

# Instance globale
audit_logger = AuditLogger()
