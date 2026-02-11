from pathlib import Path
from typing import List, Tuple

import faiss
import numpy as np


class VectorStore:
    """Stockage vectoriel simple en local basé sur FAISS."""

    def __init__(self, dim: int, store_dir: Path):
        self.dim = dim
        self.store_dir = store_dir
        self.index_path = store_dir / "index.faiss"
        self.metadata_path = store_dir / "metadata.npy"

        self.store_dir.mkdir(parents=True, exist_ok=True)

        if self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            self.metadata = np.load(self.metadata_path, allow_pickle=True).tolist()
        else:
            self.index = faiss.IndexFlatL2(dim)
            self.metadata: List[dict] = []

    def add(self, vectors: np.ndarray, metadatas: List[dict]) -> None:
        assert vectors.shape[1] == self.dim, "Dimension des vecteurs incompatible"
        self.index.add(vectors.astype("float32"))
        self.metadata.extend(metadatas)
        self._persist()

    def search(self, query_vector: np.ndarray, k: int = 5) -> List[Tuple[dict, float]]:
        query_vector = query_vector.astype("float32").reshape(1, -1)
        distances, indices = self.index.search(query_vector, k)
        results: List[Tuple[dict, float]] = []
        for idx, dist in zip(indices[0], distances[0]):
            if 0 <= idx < len(self.metadata):
                results.append((self.metadata[idx], float(dist)))
        return results

    def _persist(self) -> None:
        faiss.write_index(self.index, str(self.index_path))
        np.save(self.metadata_path, np.array(self.metadata, dtype=object), allow_pickle=True)

