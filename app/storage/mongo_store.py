from __future__ import annotations

from typing import Iterable, List, Mapping, Optional

from bson import ObjectId
from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection

from app.config.settings import settings


class MongoEnrichedDocumentStore:
    """Stockage MongoDB des documents enrichis pour la veille bancaire.

    Chaque document correspond typiquement à un texte passé par:
    - scraping,
    - nettoyage NLP,
    - enrichissement (classification, entités, résumé, etc.).

    Le schéma reste souple (dict arbitraire) pour faciliter l'évolution du PFE.
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        db_name: Optional[str] = None,
        collection_name: Optional[str] = None,
    ) -> None:
        self._uri = uri or settings.mongodb_uri
        self._db_name = db_name or settings.mongodb_db_name
        self._collection_name = collection_name or settings.mongodb_collection_enriched

        self._client = MongoClient(self._uri, serverSelectionTimeoutMS=5000)
        self._db = self._client[self._db_name]
        self._collection: Collection = self._db[self._collection_name]

        self._ensure_indexes()

    @property
    def collection(self) -> Collection:
        return self._collection

    def _ensure_indexes(self) -> None:
        """Crée les index utiles pour le moteur de veille / RAG."""
        self._collection.create_index(
            [("source_id", ASCENDING)],
            name="idx_source_id",
            background=True,
        )
        self._collection.create_index(
            [("lang", ASCENDING)],
            name="idx_lang",
            background=True,
        )
        self._collection.create_index(
            [("created_at", ASCENDING)],
            name="idx_created_at",
            background=True,
        )
        # Index texte pour la recherche par mots-clés (titre + texte)
        self._collection.create_index(
            [("title", "text"), ("text", "text")],
            name="idx_text_search",
            background=True,
        )

    # ------------------------------------------------------------------
    # Opérations de base
    # ------------------------------------------------------------------
    def save_documents(self, docs: Iterable[Mapping]) -> List[str]:
        """Insère une liste de documents enrichis.

        Args:
            docs: itérable de dictionnaires JSON-sérialisables.

        Returns:
            Liste des identifiants Mongo sous forme de chaînes.
        """
        docs_list = list(docs)
        if not docs_list:
            return []

        result = self._collection.insert_many(docs_list)
        return [str(_id) for _id in result.inserted_ids]

    def upsert_document(self, source_id: str, doc: Mapping) -> str:
        """Met à jour ou crée un document à partir d'un `source_id` logique."""
        result = self._collection.update_one(
            {"source_id": source_id},
            {"$set": dict(doc)},
            upsert=True,
        )
        if result.upserted_id is not None:
            return str(result.upserted_id)

        # Si c'était une mise à jour, on récupère l'_id correspondant
        found = self._collection.find_one({"source_id": source_id}, {"_id": 1})
        return str(found["_id"]) if found else ""

    def get_by_id(self, mongo_id: str) -> Optional[dict]:
        """Récupère un document par son _id Mongo."""
        try:
            oid = ObjectId(mongo_id)
        except Exception:  # noqa: BLE001
            return None
        doc = self._collection.find_one({"_id": oid})
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc

    def get_by_source_id(self, source_id: str) -> Optional[dict]:
        """Récupère un document par son identifiant logique source."""
        doc = self._collection.find_one({"source_id": source_id})
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc


class MongoSourceStore:
    """Stockage MongoDB des sources configurées."""

    def __init__(self, uri: Optional[str] = None, db_name: Optional[str] = None):
        self._uri = uri or settings.mongodb_uri
        self._db_name = db_name or settings.mongodb_db_name
        self._client = MongoClient(self._uri, serverSelectionTimeoutMS=5000)
        self._db = self._client[self._db_name]
        self._collection: Collection = self._db["sources"]
        self._collection.create_index([("id", ASCENDING)], unique=True)

    def save_source(self, source: dict) -> str:
        """Enregistre ou met à jour une source."""
        if "id" not in source or not source["id"]:
            import uuid
            source["id"] = str(uuid.uuid4())
        
        self._collection.update_one(
            {"id": source["id"]},
            {"$set": source},
            upsert=True
        )
        return source["id"]

    def list_sources(self) -> List[dict]:
        """Liste toutes les sources enregistrées par l'utilisateur."""
        docs = list(self._collection.find())
        for doc in docs:
            doc["_id"] = str(doc["_id"])
        return docs

    def get_source(self, source_id: str) -> Optional[dict]:
        """Récupère une source par son ID."""
        doc = self._collection.find_one({"id": source_id})
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc

    def delete_source(self, source_id: str) -> bool:
        """Supprime une source."""
        result = self._collection.delete_one({"id": source_id})
        return result.deleted_count > 0

    def init_static_sources(self):
        """Initialise ou met à jour les sources statiques dans MongoDB en copiant toutes les config."""
        from app.scraping.sources_registry import SOURCES_REGISTRY
        
        for sid, config in SOURCES_REGISTRY.items():
            # On prend tout ce qui est dans le registry
            source_doc = config.copy()
            source_doc["id"] = sid
            # On mappe certain champs pour la compatibilité UI si nécessaire
            if "base_url" in config:
                source_doc["url"] = config["base_url"]
            
            # Valeurs par défaut pour l'UI
            source_doc.setdefault("type", "Regulatory" if "gov" in source_doc["url"] or "bank" in source_doc["url"] else "Market")
            source_doc.setdefault("frequency", "Daily")
            source_doc.setdefault("status", "Active")
            
            # Upsert using id
            self._collection.update_one(
                {"id": sid},
                {"$set": source_doc},
                upsert=True
            )


class MongoSystemStore:
    """Stockage MongoDB pour les données système (Audit, Paramètres, Domaines)."""

    def __init__(self, uri: Optional[str] = None, db_name: Optional[str] = None):
        self._uri = uri or settings.mongodb_uri
        self._db_name = db_name or settings.mongodb_db_name
        self._client = MongoClient(self._uri, serverSelectionTimeoutMS=5000)
        self._db = self._client[self._db_name]
        
        self.audit_col = self._db["audit_logs"]
        self.settings_col = self._db["settings"]
        self.domains_col = self._db["whitelisted_domains"]

        # Index pour les logs
        self.audit_col.create_index([("timestamp", -1)])

    # --- Audit Logs ---
    def save_log(self, log: dict):
        """Enregistre un log d'audit."""
        if "_id" in log:
            del log["_id"]
        self.audit_col.insert_one(log)

    def get_logs(self, limit: int = 100) -> List[dict]:
        """Récupère les derniers logs."""
        return list(self.audit_col.find().sort("timestamp", -1).limit(limit))

    # --- Settings ---
    def get_settings(self) -> dict:
        """Récupère les paramètres globaux."""
        doc = self.settings_col.find_one({"_id": "global_settings"})
        if not doc:
            # Default settings
            return {
                "refreshFrequency": "hourly",
                "confidenceThreshold": 85,
                "dataRetentionDays": 365,
                "enableNotifications": True
            }
        return doc

    def update_settings(self, new_settings: dict):
        """Met à jour les paramètres."""
        new_settings["_id"] = "global_settings"
        self.settings_col.replace_one({"_id": "global_settings"}, new_settings, upsert=True)
        return new_settings

    # --- Whitelisted Domains ---
    def get_domains(self) -> List[dict]:
        """Récupère les domaines whitelistés."""
        return list(self.domains_col.find())

    def add_domain(self, domain: dict):
        """Ajoute un domaine."""
        if "id" not in domain:
            import uuid
            domain["id"] = str(uuid.uuid4())
        self.domains_col.insert_one(domain)
        return domain

