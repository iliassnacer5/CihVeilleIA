"""
Service de ré-ordonnancement (Re-ranking) multilingue pour le RAG.

Utilise un Cross-Encoder multilingue pour calculer un score de pertinence
plus précis entre la question et chaque passage récupéré.
"""

import logging
from typing import List, Tuple
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)

# Modèle multilingue — bien meilleur pour le français que la version EN-only
DEFAULT_MODEL = "cross-encoder/ms-marco-multilingual-MiniLM-L-6-v2"


class RerankingService:
    """Service de ré-ordonnancement multilingue pour optimiser le RAG.
    
    Réorganise les résultats de la recherche vectorielle en calculant
    un score de pertinence croisé (question, passage) pour chaque résultat.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL):
        logger.info(f"Loading reranking model: {model_name}...")
        try:
            self.model = CrossEncoder(model_name)
            logger.info(f"✅ Reranking model loaded: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load reranker: {e}")
            self.model = None

    def rerank(self, query: str, passages: List[str], top_n: int = 5) -> List[Tuple[int, float]]:
        """Réorganise les passages par pertinence.
        
        Args:
            query: la question de l'utilisateur.
            passages: les passages récupérés par la recherche vectorielle.
            top_n: nombre de résultats à retourner.
            
        Returns:
            Liste de tuples (index_original, score) triés par pertinence.
        """
        if not self.model or not passages:
            return [(idx, 1.0) for idx in range(len(passages[:top_n]))]

        # Préparation des paires (query, passage)
        pairs = [[query, passage] for passage in passages]
        
        # Calcul des scores
        scores = self.model.predict(pairs)
        
        # Tri par score décroissant
        results = sorted(
            enumerate(scores), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return results[:top_n]
