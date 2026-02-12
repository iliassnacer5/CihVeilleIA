import logging
import time
from typing import Dict, List, Optional

from app.storage.mongo_store import MongoAlertStore
from app.storage.audit_log import audit_logger
from app.alerts.outlook_connector import OutlookConnector

logger = logging.getLogger(__name__)

class AlertService:
    """Service intelligent pour la génération d'alertes de veille."""

    def __init__(self, alert_store: Optional[MongoAlertStore] = None):
        self.alert_store = alert_store or MongoAlertStore()
        self.outlook = OutlookConnector()
        self.manager = None
        self.confidence_threshold = 90
        self.priority_topics = ["Cybersécurité", "Réglementation", "Concurrence"]

    def set_connection_manager(self, manager):
        self.manager = manager

    async def process_new_documents(self, docs: List[Dict], user_id: str = "admin") -> int:
        """Analyse une liste de nouveaux documents et génère des alertes."""
        alerts_count = 0
        
        for doc in docs:
            # Requis: Détecter automatiquement qu'un nouveau document a été ajouté
            # On considère que chaque nouveau document mérite une notification/alerte PFE
            priority = "low"
            topics = doc.get("topics", [])
            
            if any(t in self.priority_topics for t in topics):
                priority = "high"
            elif doc.get("confidence", 0) >= self.confidence_threshold:
                priority = "medium"
            
            alert_payload = {
                "user_id": user_id,
                "title": f"Nouveau document: {doc.get('title', 'Sans titre')}",
                "message": f"Une nouvelle veille est disponible sur {doc.get('source_id')}.",
                "type": "insight",
                "priority": priority,
                "metadata": {
                    "doc_id": str(doc.get("_id")) if "_id" in doc else None,
                    "source": doc.get("source_id"),
                    "url": doc.get("url"),
                    "topics": topics,
                    "category": doc.get("category", "Général"),
                    "doc_type": doc.get("doc_type", "News"),
                    "added_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                },
                "is_read": False,
                "created_at": time.time()
            }
            
            try:
                # 1. Sauvegarde en DB
                await self.alert_store.save_alert(alert_payload)
                alerts_count += 1
                
                # 2. Notification Temps Réel UI (WebSocket)
                if self.manager:
                    await self.manager.broadcast_to_user(user_id, {
                        "type": "new_document_alert",
                        "data": alert_payload
                    })
                
                # 3. Notification E-mail Outlook (Graph API)
                # On envoie un mail pour le "high" ou selon configuration
                # Ici on force l'envoi pour tester le workflow complet
                try:
                    email_html = await self.outlook.generate_alert_html(alert_payload)
                    await self.outlook.send_alert_email(
                        to_email="iliassnacer5@gmail.com", # Placeholder final
                        subject=f"Nouveau document ajouté - {doc.get('title')}",
                        content_html=email_html
                    )
                except Exception as email_err:
                    logger.error(f"Erreur envoi email: {email_err}")
                
                # Log d'audit
                await audit_logger.log_event_async(
                    "ALERT_GENERATED", "AUTO_NOTIFY", "SUCCESS", 
                    {"priority": priority, "doc_title": doc.get("title")}
                )
            except Exception as e:
                logger.error(f"Échec du traitement de l'alerte pour {doc.get('title')}: {e}")
                
        return alerts_count

    async def get_latest_alerts(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Récupère les dernières alertes pour un utilisateur."""
        return await self.alert_store.get_user_alerts(user_id, limit=limit)
