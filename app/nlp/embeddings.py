"""
Service d'embeddings pour le moteur RAG — Multilingual E5 Large.

Utilise `intfloat/multilingual-e5-large` (1024 dimensions) pour des embeddings
multilingues de haute qualité, particulièrement performants en français et arabe.
"""

from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

# Modèle par défaut — meilleur rapport qualité/compatibilité multilingue
DEFAULT_MODEL = "intfloat/multilingual-e5-large"


class EmbeddingService:
    """Service d'embeddings haute performance pour le RAG.
    
    Le modèle E5 nécessite un prefix pour les textes:
    - "query: " pour les questions/requêtes
    - "passage: " pour les documents/passages à indexer
    """

    def __init__(self, model_name: str = DEFAULT_MODEL):
        logger.info(f"Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        self._is_e5 = "e5" in model_name.lower()
        dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"✅ Embedding model loaded: {model_name} ({dim} dimensions)")

    def encode(self, texts: List[str], is_query: bool = False) -> np.ndarray:
        """Encode une liste de textes en vecteurs.
        
        Args:
            texts: textes à encoder.
            is_query: True pour les requêtes de recherche, False pour les passages.
        """
        if self._is_e5:
            prefix = "query: " if is_query else "passage: "
            texts = [prefix + t for t in texts]
        
        return self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

    def encode_query(self, text: str) -> np.ndarray:
        """Encode une requête de recherche."""
        return self.encode([text], is_query=True)[0]

    def encode_passages(self, texts: List[str]) -> np.ndarray:
        """Encode des passages/documents pour l'indexation."""
        return self.encode(texts, is_query=False)
