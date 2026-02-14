import logging
import time
from typing import Dict, List, Optional

from app.storage.mongo_store import MongoAlertStore
from app.storage.audit_log import audit_logger
from app.notifications.service import NotificationService

logger = logging.getLogger(__name__)

class AlertService:
    """Service intelligent pour la génération d'alertes de veille."""

    def __init__(self, alert_store: Optional[MongoAlertStore] = None):
        self.alert_store = alert_store or MongoAlertStore()
        self.notification_service = NotificationService()
        self.manager = None
        self.confidence_threshold = 90
        self.priority_topics = ["Cybersécurité", "Réglementation", "Concurrence"]

    def set_connection_manager(self, manager):
        self.manager = manager

    async def process_new_documents(self, docs: List[Dict], user_id: str = "admin") -> int:
        """Analyse une liste de nouveaux documents et génère des alertes."""
        logging.info(f"--- AlertService: Processing {len(docs)} docs for {user_id} ---")
        alerts_count = 0
        
        for doc in docs:
            # 1. Calcul du score et de l'importance
            score, level = self.calculate_importance(doc)
            
            # 2. Création du payload d'alerte
            alert_payload = {
                "user_id": user_id,
                "title": f"NOUVEAU - {doc.get('title', 'Sans titre')}",
                "description": f"Document détecté : {doc.get('title')} (Source: {doc.get('source_id')}).",
                "type": "insight",
                "severity": level,   # critical, high, medium, low
                "score": score,
                "metadata": {
                    "doc_id": str(doc.get("_id")) if "_id" in doc else None,
                    "source": doc.get("source_id"),
                    "url": doc.get("url"),
                    "topics": doc.get("topics", []),
                    "category": doc.get("category", "Général"),
                    "doc_type": doc.get("doc_type", "News"),
                    "added_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                },
                "read": False,
                "created_at": time.time()
            }
            
            # Si c'est critique, on force un titre impactant
            if level == "critical":
                alert_payload["title"] = f"🚨 [CRITIQUE] {doc.get('title', 'Alerte Veille')}"
            elif level == "high":
                alert_payload["title"] = f"📢 [IMPORTANT] {doc.get('title', 'Alerte Veille')}"

            logging.info(f"--- Alert Calculated: Level={level}, Score={score} ---")
            
            try:
                # 3. Sauvegarde en DB
                saved_id = await self.alert_store.save_alert(alert_payload)
                logging.info(f"--- Alert Saved to DB: {saved_id} ---")
                alerts_count += 1
                
                # 4. Notification Temps Réel UI (WebSocket)
                if self.manager:
                    logging.info("--- Broadcasting to WebSocket ---")
                    await self.manager.broadcast_to_user(user_id, {
                        "type": "new_document_alert",
                        "data": alert_payload
                    })
                else:
                    logging.warning("--- No ConnectionManager set! ---")
                
                # 5. Notification E-mail Professionnelle (SMTP ou Graph)
                # La logique de filtrage (RAG > 0.80) est gérée par le NotificationService
                try:
                    notification_data = {
                        "doc_id": str(doc.get("_id")) if "_id" in doc else None,
                        "title": doc.get('title', 'Sans titre'),
                        "source": doc.get('source_id', 'Inconnue'),
                        "summary": doc.get('summary', 'Aucun résumé disponible.'),
                        "score": score / 100.0, # Normalisation vers 0.0 - 1.0
                        "url": doc.get('url', '#'),
                        "priority": level.upper(),
                        "date": time.strftime("%d/%m/%Y", time.localtime())
                    }
                    
                    target_email = "iliass.nacer@emsi-edu.ma"
                    # Fire-and-forget: ne pas bloquer le pipeline si l'email échoue
                    import asyncio
                    asyncio.create_task(
                        self._safe_send_notification(target_email, notification_data)
                    )
                    
                except Exception as notify_err:
                    logger.error(f"Erreur lors de l'appel au NotificationService: {notify_err}")
                
                # Log d'audit
                await audit_logger.log_event(
                    "ALERT_GENERATED", "AUTO_NOTIFY", "SUCCESS", 
                    {"priority": level, "score": score, "doc_title": doc.get("title")}
                )
            except Exception as e:
                logger.error(f"Échec du traitement de l'alerte pour {doc.get('title')}: {e}")
                
        return alerts_count

    async def _safe_send_notification(self, to_email: str, data: Dict):
        """Wrapper sécurisé pour l'envoi de notification — ne propage jamais d'erreur."""
        try:
            await self.notification_service.send_regulatory_alert(to_email, data)
        except Exception as e:
            logger.warning(f"Email notification failed silently: {e}")

    def calculate_importance(self, doc: Dict) -> tuple[int, str]:
        """Calcule un score d'importance (0-100) et retourne le niveau associé."""
        score = 0
        
        # 1. Mots-clés sensibles (+20)
        text_content = (doc.get("text") or "") + (doc.get("title") or "")
        text_lower = text_content.lower()
        
        critical_keywords = [
            "bank al-maghrib", "bam", "circulaire", "sanction", "amende", 
            "blanchiment", "lcb-ft", "fraude", "risque systémique",
            "décision réglementaire", "taux directeur"
        ]
        
        important_keywords = [
            "digitalisation", "intelligence artificielle", "concurrence", 
            "partenariat", "lancement", "nouveau produit", "crypto", "blockchain"
        ]
        
        if any(kw in text_lower for kw in critical_keywords):
            score += 40
        elif any(kw in text_lower for kw in important_keywords):
            score += 20
            
        # 2. Source officielle (+30)
        source_id = doc.get("source_id", "").lower()
        if "bam" in source_id or "central" in source_id or "gov" in source_id:
            score += 30
        
        # 3. Entités (+10)
        entities = doc.get("entities", [])
        if entities and len(entities) > 3:
             score += 10
             
        # 4. Confiance IA (+Score/2)
        confidence = doc.get("confidence", 0)
        score += int(confidence * 0.2) # Max 20 pts
        
        # Normalization
        score = min(score, 100)
        
        # Determine Level
        if score >= 75:
            return score, "critical"
        elif score >= 50:
            return score, "high"
        elif score >= 25:
            return score, "medium"
        else:
            return score, "low"

    async def get_latest_alerts(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Récupère les dernières alertes pour un utilisateur."""
        return await self.alert_store.get_user_alerts(user_id, limit=limit)
