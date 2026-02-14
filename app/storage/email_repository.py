import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
from app.storage.mongo_client import get_db

logger = logging.getLogger(__name__)

class EmailRepository:
    """Répository pour la gestion des comptes email en MongoDB."""
    
    def __init__(self):
        self.db = None
        self._collection_name = "email_accounts"

    def _get_col(self):
        if self.db is None:
            self.db = get_db()
        return self.db[self._collection_name]

    async def list_accounts(self) -> List[Dict]:
        """Liste tous les comptes (sans le mot de passe)."""
        cursor = self._get_col().find({"deleted_at": None})
        docs = await cursor.to_list(length=100)
        for doc in docs:
            doc["id"] = str(doc["_id"])
            # On retire le mot de passe pour la sécurité
            if "encrypted_password" in doc:
                del doc["encrypted_password"]
        return docs

    async def get_by_id(self, account_id: str) -> Optional[Dict]:
        """Récupère un compte par son ID (inclut le mot de passe pour le service)."""
        doc = await self._get_col().find_one({"_id": ObjectId(account_id), "deleted_at": None})
        if doc:
            doc["id"] = str(doc["_id"])
        return doc

    async def get_default(self) -> Optional[Dict]:
        """Récupère le compte par défaut actif."""
        doc = await self._get_col().find_one({"enabled": True, "is_default": True, "deleted_at": None})
        if not doc:
            # Fallback sur le premier compte actif si aucun par défaut n'est défini
            doc = await self._get_col().find_one({"enabled": True, "deleted_at": None})
        if doc:
            doc["id"] = str(doc["_id"])
        return doc

    async def create_account(self, account_data: Dict) -> str:
        """Crée un nouveau compte email."""
        account_data["created_at"] = datetime.now()
        account_data["updated_at"] = datetime.now()
        account_data["deleted_at"] = None
        
        # Si c'est le premier compte, on le met par défaut
        existing_count = await self._get_col().count_documents({"deleted_at": None})
        if existing_count == 0:
            account_data["is_default"] = True
            
        result = await self._get_col().insert_one(account_data)
        return str(result.inserted_id)

    async def update_account(self, account_id: str, update_data: Dict) -> bool:
        """Met à jour un compte email."""
        update_data["updated_at"] = datetime.now()
        
        # Si on met ce compte par défaut, on retire le flag des autres
        if update_data.get("is_default"):
            await self._get_col().update_many(
                {"_id": {"$ne": ObjectId(account_id)}},
                {"$set": {"is_default": False}}
            )
            
        result = await self._get_col().update_one(
            {"_id": ObjectId(account_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0

    async def delete_account(self, account_id: str) -> bool:
        """Supprime (soft delete) un compte email."""
        result = await self._get_col().update_one(
            {"_id": ObjectId(account_id)},
            {"$set": {"deleted_at": datetime.now(), "enabled": False, "is_default": False}}
        )
        return result.modified_count > 0
