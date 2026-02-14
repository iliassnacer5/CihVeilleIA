from datetime import datetime
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.backend.auth import get_current_admin
from app.storage.notification_store import MongoNotificationStore

router = APIRouter(prefix="/notifications", tags=["notifications"])

def get_notification_store():
    return MongoNotificationStore()

@router.get("/stats")
async def get_notification_stats(
    store: MongoNotificationStore = Depends(get_notification_store),
    current_admin: dict = Depends(get_current_admin)
):
    """Récupère les statistiques de notification pour le dashboard."""
    return await store.get_notification_stats()

@router.get("/history")
async def get_notification_history(
    limit: int = 50,
    skip: int = 0,
    store: MongoNotificationStore = Depends(get_notification_store),
    current_admin: dict = Depends(get_current_admin)
):
    """Récupère l'historique complet des notifications envoyées."""
    col = store._get_col(store._history_col)
    cursor = col.find().sort("timestamp", -1).skip(skip).limit(limit)
    logs = await cursor.to_list(length=limit)
    for log in logs:
        log["_id"] = str(log["_id"])
    return logs
