from app.storage.mongo_store import MongoAlertStore
from app.storage.audit_log import audit_logger
from app.alerts.outlook_connector import OutlookConnector

logger = logging.getLogger(__name__)

class AlertService:
    """Service intelligent pour la génération d'alertes de veille."""

    def __init__(self, alert_store: Optional[MongoAlertStore] = None):
        self.alert_store = alert_store or MongoAlertStore()
        self.outlook = OutlookConnector()
        self.confidence_threshold = 90
        self.priority_topics = ["Cybersécurité", "Réglementation", "Concurrence"]

    async def process_new_documents(self, docs: List[Dict], user_id: str = "admin") -> int:
        """Analyse une liste de nouveaux documents et génère des alertes si nécessaire."""
        alerts_count = 0
        
        for doc in docs:
            should_alert = False
            priority = "low"
            
            # 1. Alerte par thématique prioritaire
            topics = doc.get("topics", [])
            if any(t in self.priority_topics for t in topics):
                should_alert = True
                priority = "high"
            
            # 2. Alerte par score de confiance élevé (détection d'une opportunité/risque majeur)
            confidence = doc.get("confidence", 0)
            if confidence >= self.confidence_threshold:
                should_alert = True
                if priority != "high":
                    priority = "medium"
            
            if should_alert:
                alert_payload = {
                    "user_id": user_id,
                    "title": f"Alerte Veille: {doc.get('title', 'Nouveau document')}",
                    "message": f"Un nouveau document important a été détecté : {doc.get('summary', '')[:150]}...",
                    "type": "insight",
                    "priority": priority,
                    "metadata": {
                        "doc_id": str(doc.get("_id")) if "_id" in doc else None,
                        "source": doc.get("source_id"),
                        "topics": topics
                    },
                    "is_read": False,
                    "created_at": time.time()
                }
                
                try:
                    await self.alert_store.save_alert(alert_payload)
                    alerts_count += 1
                    
                    # 3. Notification E-mail pour les alertes prioritaires (Nouveau Phase 3)
                    if priority == "high":
                        email_html = await self.outlook.generate_daily_digest_html([alert_payload])
                        await self.outlook.send_alert_email(
                            to_email="ilias.nacer@cih.ma", # Placeholder user
                            subject=f"ALERTE HAUTE PRIORITÉ: {doc.get('title')}",
                            content_html=email_html
                        )

                    # Log d'audit pour la traçabilité
                    await audit_logger.log_event_async(
                        "ALERT_GENERATED",
                        "AUTO_INSIGHT",
                        "SUCCESS",
                        {"priority": priority, "topics": topics}
                    )
                except Exception as e:
                    logger.error(f"Échec de la sauvegarde de l'alerte: {e}")
                    
        return alerts_count

    async def get_latest_alerts(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Récupère les dernières alertes pour un utilisateur."""
        return await self.alert_store.get_user_alerts(user_id, limit=limit)
