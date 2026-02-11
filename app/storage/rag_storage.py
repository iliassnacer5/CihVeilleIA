from __future__ import annotations

from typing import Iterable, List, Mapping, Optional

import numpy as np

from app.config.settings import settings
from app.nlp.embeddings import EmbeddingService
from app.rag.vector_store import VectorStore
from app.storage.mongo_store import MongoEnrichedDocumentStore


class RagStorageService:
    """Service de stockage optimisé pour un moteur RAG bancaire.

    Responsabilités:
    - persister les documents enrichis dans MongoDB;
    - vectoriser les textes (embeddings);
    - indexer les vecteurs dans FAISS pour la recherche.
    """

    def __init__(
        self,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        mongo_store: Optional[MongoEnrichedDocumentStore] = None,
    ) -> None:
        self.embedding_service = EmbeddingService(model_name=embedding_model)
        self.mongo_store = mongo_store or MongoEnrichedDocumentStore()

        dummy_vector = self.embedding_service.encode(["dummy"])
        dim = int(dummy_vector.shape[1])
        self.vector_store = VectorStore(dim=dim, store_dir=settings.vector_store_dir)

    def _build_metadata(self, mongo_id: str, doc: Mapping, text: str) -> dict:
        """Construit le metadata stocké côté index vectoriel."""
        return {
            "mongo_id": mongo_id,
            "source_id": doc.get("id") or doc.get("source_id"),
            "title": doc.get("title"),
            "url": doc.get("url"),
            "lang": doc.get("lang"),
            "topics": doc.get("topics") or doc.get("labels"),
            "summary": doc.get("summary"),
            "text": text,
        }

    def index_enriched_documents(self, docs: Iterable[Mapping]) -> List[str]:
        """Persiste et indexe une collection de documents enrichis.

        Chaque document `doc` est supposé contenir au minimum une clé `text`.
        Les champs supplémentaires (classification, entités, résumé, ...) sont
        simplement stockés dans Mongo et une partie est copiée en metadata
        pour le moteur RAG.

        Args:
            docs: itérable de dictionnaires (documents enrichis).

        Returns:
            Liste des identifiants Mongo insérés.
        """
        docs_list = list(docs)
        if not docs_list:
            return []

        # 1) Sauvegarde Mongo
        mongo_ids = self.mongo_store.save_documents(docs_list)

        # 2) Préparation des textes à vectoriser + métadonnées
        texts: List[str] = []
        metadatas: List[dict] = []
        for mongo_id, doc in zip(mongo_ids, docs_list):
            text = doc.get("text") or doc.get("raw_text")
            if not text or not str(text).strip():
                continue
            text_str = str(text)
            texts.append(text_str)
            metadatas.append(self._build_metadata(mongo_id, doc, text_str))

        if not texts:
            return mongo_ids

        # 3) Vectorisation + indexation FAISS
        vectors = self.embedding_service.encode(texts)
        self.vector_store.add(vectors=np.array(vectors), metadatas=metadatas)

        return mongo_ids

