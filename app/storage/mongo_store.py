from __future__ import annotations

import logging
import uuid
import time
from datetime import datetime
from typing import Any, Dict, Iterable, List, Mapping, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pymongo import ASCENDING, DESCENDING

from app.config.settings import settings

logger = logging.getLogger(__name__)

class BaseMongoStore:
    """Classe de base asynchrone pour les interactions MongoDB."""
    
    def __init__(
        self,
        uri: Optional[str] = None,
        db_name: Optional[str] = None,
        collection_name: str = "default",
        client: Optional[AsyncIOMotorClient] = None,
    ) -> None:
        self._uri = uri or settings.mongodb_uri
        self._db_name = db_name or settings.mongodb_db_name
        self._collection_name = collection_name

        if client:
            self._client = client
        else:
            self._client = AsyncIOMotorClient(self._uri, serverSelectionTimeoutMS=5000)
            
        self._db = self._client[self._db_name]
        self._collection: AsyncIOMotorCollection = self._db[self._collection_name]

    async def close(self):
        if self._client:
            self._client.close()

    @property
    def collection(self) -> AsyncIOMotorCollection:
        return self._collection

class MongoEnrichedDocumentStore(BaseMongoStore):
    """Stockage MongoDB asynchrone des documents enrichis."""

    def __init__(self, **kwargs) -> None:
        kwargs.setdefault("collection_name", settings.mongodb_collection_enriched)
        super().__init__(**kwargs)

    async def ensure_indexes(self) -> None:
        """Crée les index utiles pour le moteur de veille / RAG."""
        await self._collection.create_index([("source_id", ASCENDING)], name="idx_source_id", background=True)
        await self._collection.create_index([("lang", ASCENDING)], name="idx_lang", background=True)
        await self._collection.create_index([("created_at", ASCENDING)], name="idx_created_at", background=True)
        await self._collection.create_index([("url", ASCENDING)], name="idx_url", unique=True, background=True)
        await self._collection.create_index(
            [("title", "text"), ("text", "text")],
            name="idx_text_search",
            background=True,
        )

    async def save_documents(self, docs: Iterable[Mapping]) -> List[str]:
        """Sauvegarde des documents avec détection de doublons basée sur l'URL."""
        docs_list = list(docs)
        if not docs_list:
            return []
        
        saved_ids = []
        for doc in docs_list:
            # Upsert: met à jour si l'URL existe déjà, sinon insère
            result = await self._collection.update_one(
                {"url": doc.get("url")},
                {"$set": doc},
                upsert=True
            )
            # Récupère l'ID (soit celui inséré, soit celui existant)
            if result.upserted_id:
                saved_ids.append(str(result.upserted_id))
            else:
                # Document déjà existant, récupère son ID
                existing = await self._collection.find_one({"url": doc.get("url")})
                if existing:
                    saved_ids.append(str(existing["_id"]))
        
        return saved_ids

    async def delete_documents(self, mongo_ids: List[str]) -> int:
        """Supprime un ou plusieurs documents par leurs IDs MongoDB."""
        oids = []
        for mid in mongo_ids:
            try:
                oids.append(ObjectId(mid))
            except Exception:
                logger.warning(f"ID MongoDB invalide ignoré pour suppression: {mid}")
        
        if not oids:
            return 0
            
        result = await self._collection.delete_many({"_id": {"$in": oids}})
        return result.deleted_count

    async def upsert_document(self, source_id: str, doc: Mapping) -> str:
        result = await self._collection.update_one(
            {"source_id": source_id},
            {"$set": dict(doc)},
            upsert=True,
        )
        if result.upserted_id is not None:
            return str(result.upserted_id)
        found = await self._collection.find_one({"source_id": source_id}, {"_id": 1})
        return str(found["_id"]) if found else ""

    async def get_by_id(self, mongo_id: str) -> Optional[dict]:
        try:
            oid = ObjectId(mongo_id)
        except Exception:
            return None
        doc = await self._collection.find_one({"_id": oid})
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc

class MongoSourceStore(BaseMongoStore):
    """Stockage MongoDB asynchrone des sources."""

    def __init__(self, **kwargs) -> None:
        kwargs.setdefault("collection_name", "sources")
        super().__init__(**kwargs)

    async def ensure_indexes(self) -> None:
        await self._collection.create_index([("id", ASCENDING)], unique=True)

    async def save_source(self, source: dict) -> str:
        if "id" not in source or not source["id"]:
            source["id"] = str(uuid.uuid4())
        await self._collection.update_one({"id": source["id"]}, {"$set": source}, upsert=True)
        return source["id"]

    async def list_sources(self) -> List[dict]:
        cursor = self._collection.find()
        docs = await cursor.to_list(length=1000)
        for doc in docs:
            doc["_id"] = str(doc["_id"])
        return docs

    async def get_source(self, source_id: str) -> Optional[dict]:
        doc = await self._collection.find_one({"id": source_id})
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc

    async def delete_source(self, source_id: str) -> bool:
        result = await self._collection.delete_one({"id": source_id})
        return result.deleted_count > 0

    async def update_source_timestamp(self, source_id: str):
        """Met à jour l'horodatage de la dernière opération de scraping."""
        await self._collection.update_one(
            {"id": source_id},
            {"$set": {"lastUpdated": time.time()}}
        )

    async def init_static_sources(self):
        from app.scraping.sources_registry import SOURCES_REGISTRY
        for sid, config in SOURCES_REGISTRY.items():
            source_doc = config.copy()
            source_doc["id"] = sid
            if "base_url" in config:
                source_doc["url"] = config["base_url"]
            source_doc.setdefault("type", "Regulatory" if "gov" in source_doc["url"] or "bank" in source_doc["url"] else "Market")
            source_doc.setdefault("frequency", "Daily")
            source_doc.setdefault("status", "Active")
            await self._collection.update_one({"id": sid}, {"$set": source_doc}, upsert=True)

class MongoUserStore(BaseMongoStore):
    """Stockage des utilisateurs et de leurs préférences pour la production bancaire."""

    def __init__(self, **kwargs) -> None:
        kwargs.setdefault("collection_name", "users")
        super().__init__(**kwargs)

    async def ensure_indexes(self) -> None:
        await self._collection.create_index([("username", ASCENDING)], unique=True)
        await self._collection.create_index([("email", ASCENDING)], unique=True)

    async def get_user_by_username(self, username: str) -> Optional[dict]:
        user = await self._collection.find_one({"username": username})
        if user:
            user["id"] = str(user["_id"])
        return user

    async def list_users(self, skip: int = 0, limit: int = 50, filters: dict = None) -> List[dict]:
        query = {}
        if filters:
            if "role" in filters:
                query["role"] = filters["role"]
            if "is_active" in filters:
                query["is_active"] = filters["is_active"]
            if "search" in filters:
                query["$or"] = [
                    {"username": {"$regex": filters["search"], "$options": "i"}},
                    {"email": {"$regex": filters["search"], "$options": "i"}}
                ]
        
        cursor = self._collection.find(query).skip(skip).limit(limit).sort("created_at", DESCENDING)
        docs = await cursor.to_list(length=limit)
        for doc in docs:
            doc["id"] = str(doc["_id"])
            if "hashed_password" in doc:
                del doc["hashed_password"]
        return docs

    async def count_users(self, filters: dict = None) -> int:
        query = {}
        if filters:
            # Shared logic with list_users
            if "role" in filters:
                query["role"] = filters["role"]
            if "is_active" in filters:
                query["is_active"] = filters["is_active"]
            if "search" in filters:
                query["$or"] = [
                    {"username": {"$regex": filters["search"], "$options": "i"}},
                    {"email": {"$regex": filters["search"], "$options": "i"}}
                ]
        return await self._collection.count_documents(query)

    async def create_user(self, user_data: dict) -> str:
        user_data["created_at"] = datetime.utcnow()
        user_data.setdefault("is_active", True)
        result = await self._collection.insert_one(user_data)
        return str(result.inserted_id)

    async def update_user(self, username: str, update_data: dict):
        await self._collection.update_one({"username": username}, {"$set": update_data})

    async def update_last_login(self, username: str):
        await self._collection.update_one(
            {"username": username}, 
            {"$set": {"last_login": datetime.utcnow()}}
        )

    async def delete_user(self, username: str):
        await self._collection.delete_one({"username": username})

class MongoAlertStore(BaseMongoStore):
    """Stockage persistant des alertes et des abonnements utilisateurs."""

    def __init__(self, **kwargs) -> None:
        kwargs.setdefault("collection_name", "alerts")
        super().__init__(**kwargs)

    async def ensure_indexes(self) -> None:
        await self._collection.create_index([("user_id", ASCENDING)])
        await self._collection.create_index([("created_at", DESCENDING)])
        await self._collection.create_index([("read", ASCENDING)])

    async def save_alert(self, alert_data: dict) -> str:
        alert_data.setdefault("created_at", time.time())
        alert_data.setdefault("read", False)
        result = await self._collection.insert_one(alert_data)
        return str(result.inserted_id)

    async def get_user_alerts(self, user_id: str, limit: int = 50) -> List[dict]:
        cursor = self._collection.find({"user_id": user_id}).sort("created_at", DESCENDING).limit(limit)
        docs = await cursor.to_list(length=limit)
        for doc in docs:
            doc["_id"] = str(doc["_id"])
        return docs

    async def mark_as_read(self, alert_id: str):
        await self._collection.update_one({"_id": ObjectId(alert_id)}, {"$set": {"read": True}})

    async def count_unread_alerts(self, user_id: str) -> int:
        """Compte le nombre d'alertes non lues pour un utilisateur."""
        return await self._collection.count_documents({"user_id": user_id, "read": False})

class MongoSystemStore(BaseMongoStore):
    """Stockage MongoDB pour les données système (Audit, Paramètres)."""

    def __init__(self, **kwargs) -> None:
        kwargs.setdefault("collection_name", "system") # Not used directly as it has multiple collections
        super().__init__(**kwargs)
        self.audit_col = self._db["audit_logs"]
        self.settings_col = self._db["settings"]
        self.domains_col = self._db["whitelisted_domains"]

    async def ensure_indexes(self) -> None:
        await self.audit_col.create_index([("timestamp", DESCENDING)])

    async def save_log(self, log: dict):
        if "_id" in log:
            del log["_id"]
        await self.audit_col.insert_one(log)

    async def get_logs(self, limit: int = 100) -> List[dict]:
        cursor = self.audit_col.find().sort("timestamp", DESCENDING).limit(limit)
        docs = await cursor.to_list(length=limit)
        for d in docs:
            d["id"] = str(d["_id"])
        return docs

    async def get_settings(self) -> dict:
        doc = await self.settings_col.find_one({"_id": "global_settings"})
        if not doc:
            return {
                "refreshFrequency": "hourly",
                "confidenceThreshold": 85,
                "dataRetentionDays": 365,
                "enableNotifications": True
            }
        return doc

    async def update_settings(self, new_settings: dict):
        new_settings["_id"] = "global_settings"
        await self.settings_col.replace_one({"_id": "global_settings"}, new_settings, upsert=True)
        return new_settings

    async def get_domains(self) -> List[dict]:
        cursor = self.domains_col.find()
        docs = await cursor.to_list(length=100)
        for d in docs:
            d["_id"] = str(d["_id"])
        return docs

    async def add_domain(self, domain: dict):
        if "id" not in domain:
            domain["id"] = str(uuid.uuid4())
        await self.domains_col.insert_one(domain)
        return domain
