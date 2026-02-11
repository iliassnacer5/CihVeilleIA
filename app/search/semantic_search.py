from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional, Sequence

import numpy as np

from app.config.settings import settings
from app.nlp.embeddings import EmbeddingService
from app.rag.vector_store import VectorStore
from app.storage.mongo_store import MongoEnrichedDocumentStore


@dataclass
class SearchFilters:
    """Filtres applicables aux recherches de veille bancaire."""

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    sources: Optional[List[str]] = None
    topics: Optional[List[str]] = None
    lang: Optional[str] = None


@dataclass
class SearchResult:
    """Résultat de recherche unifié pour l'interface utilisateur."""

    mongo_id: Optional[str]
    title: Optional[str]
    url: Optional[str]
    summary: Optional[str]
    text_snippet: Optional[str]
    source_id: Optional[str]
    lang: Optional[str]
    topics: Optional[List[str]]
    score: float
    score_type: str  # "keyword" ou "vector"


class SemanticSearchEngine:
    """Moteur de recherche sémantique pour la veille IA bancaire.

    Fonctionnalités:
    - recherche par mots-clés (MongoDB / index texte) ;
    - recherche par similarité vectorielle (FAISS) ;
    - filtrage par date, source, thématique, langue ;
    - résultats unifiés prêts pour un frontend.
    """

    def __init__(
        self,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        mongo_store: Optional[MongoEnrichedDocumentStore] = None,
    ) -> None:
        self.mongo_store = mongo_store or MongoEnrichedDocumentStore()
        self.embedding_service = EmbeddingService(model_name=embedding_model)

        dummy_vector = self.embedding_service.encode(["dummy"])
        dim = int(dummy_vector.shape[1])
        self.vector_store = VectorStore(dim=dim, store_dir=settings.vector_store_dir)

    # ------------------------------------------------------------------
    # Recherche par mots-clés (MongoDB)
    # ------------------------------------------------------------------
    def keyword_search(
        self,
        query: str,
        filters: Optional[SearchFilters] = None,
        limit: int = 20,
    ) -> List[SearchResult]:
        """Recherche plein texte avec filtres via MongoDB.

        Nécessite un index texte MongoDB sur les champs `title` et `text`.
        """
        if not query or not query.strip():
            return []

        mongo_query: dict = {"$text": {"$search": query}}
        filters = filters or SearchFilters()

        if filters.lang:
            mongo_query["lang"] = filters.lang

        if filters.sources:
            mongo_query["source"] = {"$in": filters.sources}

        if filters.topics:
            mongo_query["topics"] = {"$in": filters.topics}

        if filters.start_date or filters.end_date:
            date_filter: dict = {}
            if filters.start_date:
                date_filter["$gte"] = filters.start_date
            if filters.end_date:
                date_filter["$lte"] = filters.end_date
            mongo_query["created_at"] = date_filter

        cursor = self.mongo_store.collection.find(
            mongo_query,
            {
                "_id": 1,
                "title": 1,
                "url": 1,
                "summary": 1,
                "text": 1,
                "source_id": 1,
                "source": 1,
                "lang": 1,
                "topics": 1,
                "score": {"$meta": "textScore"},
            },
        ).sort("score", {"$meta": "textScore"}).limit(limit)

        results: List[SearchResult] = []
        for doc in cursor:
            text = doc.get("summary") or doc.get("text") or ""
            snippet = text[:400] + ("..." if len(text) > 400 else "")
            results.append(
                SearchResult(
                    mongo_id=str(doc["_id"]),
                    title=doc.get("title"),
                    url=doc.get("url"),
                    summary=doc.get("summary"),
                    text_snippet=snippet,
                    source_id=doc.get("source_id") or doc.get("source"),
                    lang=doc.get("lang"),
                    topics=doc.get("topics"),
                    score=float(doc.get("score", 0.0)),
                    score_type="keyword",
                )
            )

        return results

    # ------------------------------------------------------------------
    # Recherche vectorielle (FAISS)
    # ------------------------------------------------------------------
    def vector_search(
        self,
        query: str,
        filters: Optional[SearchFilters] = None,
        top_k: int = 10,
        oversampling_factor: int = 5,
    ) -> List[SearchResult]:
        """Recherche sémantique par similarité vectorielle."""
        if not query or not query.strip():
            return []

        filters = filters or SearchFilters()

        query_vec = self.embedding_service.encode([query])[0]
        # On prend un peu plus de résultats, puis on filtre
        raw_results = self.vector_store.search(
            np.array(query_vec),
            k=top_k * oversampling_factor,
        )

        def _passes_filters(meta: dict) -> bool:
            if filters.lang and meta.get("lang") != filters.lang:
                return False
            if filters.sources and meta.get("source_id") not in filters.sources:
                return False
            if filters.topics:
                meta_topics = meta.get("topics") or []
                if not any(t in meta_topics for t in filters.topics):
                    return False
            # Pour le filtrage par date, on s'appuie typiquement sur Mongo;
            # ici on filtre uniquement sur metadata si disponible.
            return True

        results: List[SearchResult] = []
        for meta, dist in raw_results:
            if not _passes_filters(meta):
                continue

            text = meta.get("summary") or meta.get("text") or ""
            snippet = text[:400] + ("..." if len(text) > 400 else "")

            # Transforme une distance L2 en score de similarité simple
            score = 1.0 / (1.0 + float(dist))

            results.append(
                SearchResult(
                    mongo_id=meta.get("mongo_id"),
                    title=meta.get("title"),
                    url=meta.get("url"),
                    summary=meta.get("summary"),
                    text_snippet=snippet,
                    source_id=meta.get("source_id"),
                    lang=meta.get("lang"),
                    topics=meta.get("topics"),
                    score=score,
                    score_type="vector",
                )
            )

            if len(results) >= top_k:
                break

        return results

    # ------------------------------------------------------------------
    # Recherche hybride (optionnelle pour futur UI)
    # ------------------------------------------------------------------
    def hybrid_search(
        self,
        query: str,
        filters: Optional[SearchFilters] = None,
        keyword_weight: float = 0.4,
        vector_weight: float = 0.6,
        limit: int = 20,
    ) -> List[SearchResult]:
        """Combine recherche par mots-clés et vectorielle.

        Stratégie simple:
        - on normalise les scores des deux listes;
        - on fusionne sur `mongo_id`/`url` quand possible;
        - on garde les `limit` meilleurs résultats agrégés.
        """
        filters = filters or SearchFilters()

        keyword_results = self.keyword_search(query, filters=filters, limit=limit)
        vector_results = self.vector_search(query, filters=filters, top_k=limit)

        def _normalize(scores: List[float]) -> List[float]:
            if not scores:
                return []
            min_s, max_s = min(scores), max(scores)
            if max_s == min_s:
                return [1.0 for _ in scores]
            return [(s - min_s) / (max_s - min_s) for s in scores]

        kw_scores = _normalize([r.score for r in keyword_results])
        vec_scores = _normalize([r.score for r in vector_results])

        # indexation par clé logique (mongo_id ou url)
        combined: dict[str, SearchResult] = {}
        kw_map = {}
        for r, s in zip(keyword_results, kw_scores):
            key = r.mongo_id or (r.url or "")
            kw_map[key] = s
            combined[key] = r

        for r, s in zip(vector_results, vec_scores):
            key = r.mongo_id or (r.url or "")
            existing_kw_score = kw_map.get(key, 0.0)
            hybrid_score = keyword_weight * existing_kw_score + vector_weight * s

            if key in combined:
                # fusion des infos
                base = combined[key]
                combined[key] = SearchResult(
                    mongo_id=base.mongo_id or r.mongo_id,
                    title=base.title or r.title,
                    url=base.url or r.url,
                    summary=base.summary or r.summary,
                    text_snippet=base.text_snippet or r.text_snippet,
                    source_id=base.source_id or r.source_id,
                    lang=base.lang or r.lang,
                    topics=base.topics or r.topics,
                    score=hybrid_score,
                    score_type="hybrid",
                )
            else:
                r.score = hybrid_score
                r.score_type = "hybrid"
                combined[key] = r

        # Trie global sur le score hybride
        final_results = sorted(combined.values(), key=lambda r: r.score, reverse=True)
        return final_results[:limit]

