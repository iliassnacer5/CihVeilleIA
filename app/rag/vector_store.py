"""
Stockage vectoriel FAISS pour le RAG.

Gère automatiquement le changement de dimension des embeddings:
si l'ancien index a une dimension différente, il est recréé.
"""

from pathlib import Path
from typing import List, Tuple
import logging

import faiss
import numpy as np

logger = logging.getLogger(__name__)


class VectorStore:
    """Stockage vectoriel simple en local basé sur FAISS."""

    def __init__(self, dim: int, store_dir: Path):
        self.dim = dim
        self.store_dir = store_dir
        self.index_path = store_dir / "index.faiss"
        self.metadata_path = store_dir / "metadata.npy"

        self.store_dir.mkdir(parents=True, exist_ok=True)

        if self.index_path.exists():
            existing_index = faiss.read_index(str(self.index_path))
            if existing_index.d == dim:
                self.index = existing_index
                self.metadata = np.load(self.metadata_path, allow_pickle=True).tolist()
                logger.info(f"FAISS index loaded: {self.index.ntotal} vectors ({dim}D)")
            else:
                # Dimension change — rebuild index
                logger.warning(
                    f"⚠️ FAISS dimension changed ({existing_index.d} → {dim}). "
                    f"Rebuilding index (old vectors discarded)."
                )
                self.index = faiss.IndexFlatL2(dim)
                self.metadata: List[dict] = []
                self._persist()
        else:
            self.index = faiss.IndexFlatL2(dim)
            self.metadata: List[dict] = []
            logger.info(f"New FAISS index created ({dim}D)")

    def add(self, vectors: np.ndarray, metadatas: List[dict]) -> None:
        assert vectors.shape[1] == self.dim, f"Dimension mismatch: got {vectors.shape[1]}, expected {self.dim}"
        self.index.add(vectors.astype("float32"))
        self.metadata.extend(metadatas)
        self._persist()

    def search(self, query_vector: np.ndarray, k: int = 5) -> List[Tuple[dict, float]]:
        if self.index.ntotal == 0:
            return []
        query_vector = query_vector.astype("float32").reshape(1, -1)
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_vector, k)
        results: List[Tuple[dict, float]] = []
        for idx, dist in zip(indices[0], distances[0]):
            if 0 <= idx < len(self.metadata):
                results.append((self.metadata[idx], float(dist)))
        return results

    def _persist(self) -> None:
        faiss.write_index(self.index, str(self.index_path))
        np.save(self.metadata_path, np.array(self.metadata, dtype=object), allow_pickle=True)
