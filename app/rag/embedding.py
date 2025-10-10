# app/rag/embedding.py
import os
from typing import List
import numpy as np
from fastembed import TextEmbedding

# Small, accurate, fast CPU model (~90MB on first download)
_DEFAULT_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5")

class Embedder:
    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or _DEFAULT_MODEL
        # FastEmbed lazily downloads the model on first use (cached)
        self.model = TextEmbedding(model_name=self.model_name)

    @property
    def dim(self) -> int:
        # FastEmbed exposes dimensionality via metadata; we infer after one call if needed
        return 384  # bge-small-en-v1.5

    def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        # Returns a generator of numpy arrays
        vecs = list(self.model.embed(texts))
        if vecs and isinstance(vecs[0], np.ndarray):
            return [v.tolist() for v in vecs]
        return vecs
