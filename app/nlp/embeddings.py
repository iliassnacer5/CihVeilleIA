from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """Service d'embeddings pour le moteur RAG."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: List[str]) -> np.ndarray:
        """Encode une liste de textes en vecteurs."""
        return self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

