import logging
import time
from datetime import datetime
from typing import Dict, List, Optional
from app.storage.mongo_client import get_db

logger = logging.getLogger(__name__)

class MongoNotificationStore:
    """Stockage persistant pour l'historique et les règles de notification."""
    
    def __init__(self):
        self.db = None
        self._history_col = "notification_history"
        self._rules_col = "notification_rules"

    def _get_col(self, col_name: str):
        if self.db is None:
            self.db = get_db()
        return self.db[col_name]

    async def log_notification(self, log_entry: Dict):
        """Enregistre un événement de notification."""
        col = self._get_col(self._history_col)
        await col.insert_one(log_entry)

    async def was_sent_recently(self, content_hash: str, window_seconds: int) -> bool:
        """Vérifie si une notification identique a été envoyée récemment."""
        col = self._get_col(self._history_col)
        since = datetime.fromtimestamp(time.time() - window_seconds)
        
        count = await col.count_documents({
            "content_hash": content_hash,
            "status": "SUCCESS",
            "timestamp": {"$gt": since}
        })
        return count > 0

    async def get_notification_stats(self) -> Dict:
        """Récupère les statistiques pour le tableau de bord."""
        col = self._get_col(self._history_col)
        
        total_sent = await col.count_documents({"status": "SUCCESS"})
        total_failed = await col.count_documents({"status": "FAILED"})
        
        # Aggregation pour les sources les plus actives
        pipeline = [
            {"$match": {"status": "SUCCESS"}},
            {"$group": {"_id": "$metadata.source", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        active_sources = await col.aggregate(pipeline).to_list(length=5)
        
        # Score moyen
        score_pipeline = [
            {"$match": {"status": "SUCCESS", "metadata.score": {"$exists": True}}},
            {"$group": {"_id": None, "avg_score": {"$avg": "$metadata.score"}}}
        ]
        avg_score_res = await col.aggregate(score_pipeline).to_list(length=1)
        avg_score = avg_score_res[0]["avg_score"] if avg_score_res else 0
        
        return {
            "total_sent": total_sent,
            "total_failed": total_failed,
            "active_sources": active_sources,
            "avg_score": round(avg_score, 2)
        }
