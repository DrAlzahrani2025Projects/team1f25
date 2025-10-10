# app/rag/retriever.py
import os, chromadb
from typing import List, Dict
from app.rag.embedding import Embedder

DATA_DIR = os.getenv("DATA_DIR", "/data")
CHROMA_DIR = os.path.join(DATA_DIR, "chroma")
COLLECTION = os.getenv("CHROMA_COLLECTION", "csusb_primo")

class Retriever:
    def __init__(self, top_k: int = 6):
        self.client = chromadb.PersistentClient(path=CHROMA_DIR)
        self.coll = self.client.get_or_create_collection(COLLECTION)
        self.embedder = Embedder()
        self.top_k = top_k

    def query(self, question: str) -> List[Dict]:
        qemb = self.embedder.embed([question])[0]
        res = self.coll.query(query_embeddings=[qemb], n_results=self.top_k, include=["documents", "metadatas", "distances"])
        out = []
        for i in range(len(res["ids"][0])):
            out.append({
                "text": res["documents"][0][i],
                "meta": res["metadatas"][0][i],
                "score": float(res["distances"][0][i])  # cosine distance (lower is better) if normalized
            })
        return out
