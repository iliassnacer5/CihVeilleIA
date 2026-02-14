import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from pymongo import DESCENDING
from app.storage.mongo_client import get_db

logger = logging.getLogger(__name__)

class AuditRepository:
    def __init__(self):
        self.db = get_db()
        self.collection = self.db["audit_logs"]

    async def ensure_indexes(self):
        await self.collection.create_index([("timestamp", DESCENDING)])
        await self.collection.create_index([("user_id", 1)])
        await self.collection.create_index([("module", 1)])
        await self.collection.create_index([("action", 1)])
        await self.collection.create_index([("status", 1)])

    async def save_log(self, log_entry: Dict[str, Any]) -> str:
        if "timestamp" not in log_entry:
            log_entry["timestamp"] = datetime.utcnow().timestamp()
        result = await self.collection.insert_one(log_entry)
        return str(result.inserted_id)

    async def list_logs(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        query = {}
        if filters:
            if filters.get("user_id"):
                query["user_id"] = filters["user_id"]
            if filters.get("module"):
                query["module"] = filters["module"]
            if filters.get("action"):
                query["action"] = filters["action"]
            if filters.get("status"):
                query["status"] = filters["status"]
            if filters.get("start_date") or filters.get("end_date"):
                query["timestamp"] = {}
                if filters.get("start_date"):
                    query["timestamp"]["$gte"] = filters["start_date"]
                if filters.get("end_date"):
                    query["timestamp"]["$lte"] = filters["end_date"]
            if filters.get("search"):
                s = filters["search"]
                query["$or"] = [
                    {"username": {"$regex": s, "$options": "i"}},
                    {"details.message": {"$regex": s, "$options": "i"}},
                    {"action": {"$regex": s, "$options": "i"}}
                ]

        cursor = self.collection.find(query).skip(skip).limit(limit).sort("timestamp", DESCENDING)
        logs = await cursor.to_list(length=limit)
        for log in logs:
            log["id"] = str(log["_id"])
            del log["_id"]
        return logs

    async def count_logs(self, filters: Dict[str, Any] = None) -> int:
        query = {}
        # ... logic similar to list_logs ...
        if filters:
            if filters.get("user_id"):
                query["user_id"] = filters["user_id"]
            if filters.get("module"):
                query["module"] = filters["module"]
            if filters.get("action"):
                query["action"] = filters["action"]
            if filters.get("status"):
                query["status"] = filters["status"]
            # ... and so on ...
        return await self.collection.count_documents(query)
