"""Pluggable text embedder.

Backends (selected by EMBEDDER env var or availability):
  * sentence-transformers (default) — real local embeddings, free, offline. Needs torch.
  * openai                          — OpenAI embeddings (uses your tokens).
  * tfidf                           — lightweight fallback so the test suite runs with no
                                      heavy deps / no network. Not as good, but same interface.
All expose .fit(corpus_texts) (no-op for ST/OpenAI) and .encode(list[str]) -> np.ndarray.
"""
from __future__ import annotations
import os, numpy as np

class Embedder:
    name = "base"
    def fit(self, corpus_texts): pass
    def encode(self, texts): raise NotImplementedError

class SentenceTransformerEmbedder(Embedder):
    name = "sentence-transformers"
    def __init__(self, model="all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model)
    def encode(self, texts):
        return np.asarray(self.model.encode(list(texts), normalize_embeddings=True))

class OpenAIEmbedder(Embedder):
    name = "openai"
    def __init__(self, model=None):
        from openai import OpenAI
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.model = model or os.environ.get("OPENAI_EMBED_MODEL", "text-embedding-3-large")
    def encode(self, texts):
        r = self.client.embeddings.create(model=self.model, input=list(texts))
        v = np.asarray([d.embedding for d in r.data])
        return v / (np.linalg.norm(v, axis=1, keepdims=True) + 1e-9)

class TfidfEmbedder(Embedder):
    name = "tfidf"
    def __init__(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.vec = TfidfVectorizer(stop_words="english")
        self._fitted = False
    def fit(self, corpus_texts):
        self.vec.fit(corpus_texts); self._fitted = True
    def encode(self, texts):
        m = self.vec.transform(list(texts)).toarray().astype(float)
        return m / (np.linalg.norm(m, axis=1, keepdims=True) + 1e-9)

def get_embedder(name: str | None = None) -> Embedder:
    name = (name or os.environ.get("EMBEDDER", "sentence-transformers")).lower()
    try:
        if name == "sentence-transformers": return SentenceTransformerEmbedder()
        if name == "openai": return OpenAIEmbedder()
        if name == "tfidf": return TfidfEmbedder()
    except Exception as e:
        print(f"[embeddings] '{name}' unavailable ({e}); falling back to tfidf.")
    return TfidfEmbedder()
