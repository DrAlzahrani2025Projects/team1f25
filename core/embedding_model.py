# core/embedding_model.py
from typing import List
from fastembed import TextEmbedding

class Embedder:
    def __init__(self, model: str = "BAAI/bge-base-en-v1.5"):
        self.model = TextEmbedding(model)

    def embed(self, texts: List[str]) -> List[List[float]]:
        # returns List[List[float]]
        return [vec for vec in self.model.embed(texts)]
