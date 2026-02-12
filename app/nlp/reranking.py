import logging
from typing import List, Tuple
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)

class RerankingService:
    """Service de ré-ordonnancement (Re-ranking) pour optimiser le RAG.
    
    Utilise un modèle de Cross-Encoder pour calculer un score de pertinence
    plus précis entre la question et chaque passage récupéré par la recherche vectorielle.
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        logger.info(f"Chargement du modèle de reranking: {model_name}...")
        try:
            self.model = CrossEncoder(model_name)
        except Exception as e:
            logger.error(f"Erreur lors du chargement du re-ranker: {e}")
            self.model = None

    def rerank(self, query: str, passages: List[str], top_n: int = 5) -> List[Tuple[int, float]]:
        """Réorganise les passages par pertinence.
        
        Retourne une liste de tuples (index_original, score).
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
