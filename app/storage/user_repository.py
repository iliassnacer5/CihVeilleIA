import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING
from app.storage.mongo_client import get_db

logger = logging.getLogger(__name__)

class UserRepository:
    def __init__(self):
        self.db = get_db()
        self.collection = self.db["users"]

    async def ensure_indexes(self):
        await self.collection.create_index([("username", ASCENDING)], unique=True)
        await self.collection.create_index([("email", ASCENDING)], unique=True)
        await self.collection.create_index([("deleted_at", ASCENDING)])

    async def get_by_username(self, username: str, include_deleted: bool = False) -> Optional[Dict[str, Any]]:
        query = {"username": username}
        if not include_deleted:
            query["deleted_at"] = None
        user = await self.collection.find_one(query)
        if user:
            user["id"] = str(user["_id"])
        return user

    async def get_by_email(self, email: str, include_deleted: bool = False) -> Optional[Dict[str, Any]]:
        query = {"email": email}
        if not include_deleted:
            query["deleted_at"] = None
        user = await self.collection.find_one(query)
        if user:
            user["id"] = str(user["_id"])
        return user

    async def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            user = await self.collection.find_one({"_id": ObjectId(user_id), "deleted_at": None})
            if user:
                user["id"] = str(user["_id"])
            return user
        except Exception:
            return None

    async def create(self, user_data: Dict[str, Any]) -> str:
        user_data["created_at"] = datetime.utcnow()
        user_data["updated_at"] = datetime.utcnow()
        user_data["deleted_at"] = None
        user_data.setdefault("is_active", True)
        result = await self.collection.insert_one(user_data)
        return str(result.inserted_id)

    async def update(self, username: str, update_data: Dict[str, Any]) -> bool:
        update_data["updated_at"] = datetime.utcnow()
        result = await self.collection.update_one(
            {"username": username, "deleted_at": None},
            {"$set": update_data}
        )
        return result.modified_count > 0

    async def soft_delete(self, username: str) -> bool:
        result = await self.collection.update_one(
            {"username": username, "deleted_at": None},
            {"$set": {"deleted_at": datetime.utcnow(), "is_active": False}}
        )
        return result.modified_count > 0

    async def list_users(
        self, 
        skip: int = 0, 
        limit: int = 50, 
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        query = {"deleted_at": None}
        if filters:
            if filters.get("role"):
                query["role"] = filters["role"]
            if filters.get("is_active") is not None:
                query["is_active"] = filters["is_active"]
            if filters.get("search"):
                s = filters["search"]
                query["$or"] = [
                    {"username": {"$regex": s, "$options": "i"}},
                    {"email": {"$regex": s, "$options": "i"}}
                ]

        cursor = self.collection.find(query).skip(skip).limit(limit).sort("created_at", DESCENDING)
        users = await cursor.to_list(length=limit)
        for user in users:
            user["id"] = str(user["_id"])
            if "hashed_password" in user:
                del user["hashed_password"]
        return users

    async def count_users(self, filters: Dict[str, Any] = None) -> int:
        query = {"deleted_at": None}
        if filters:
            if filters.get("role"):
                query["role"] = filters["role"]
            if filters.get("is_active") is not None:
                query["is_active"] = filters["is_active"]
            if filters.get("search"):
                s = filters["search"]
                query["$or"] = [
                    {"username": {"$regex": s, "$options": "i"}},
                    {"email": {"$regex": s, "$options": "i"}}
                ]
        return await self.collection.count_documents(query)
