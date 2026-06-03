"""Vector store for the DOCUMENT corpus (the RAG side).

Demonstrates the production retrieval pipeline locally:
  metadata filtering  ->  hybrid search (vector + BM25 keyword)  ->  cross-encoder rerank.
Numbers are NOT stored here — only narrative/policy text.
"""
from __future__ import annotations
import os, glob, re, numpy as np
from dataclasses import dataclass, field

@dataclass
class Chunk:
    chunk_id: str
    text: str
    metadata: dict
    vector: np.ndarray = None
    score: float = 0.0

def _chunk_text(body: str, max_words=90):
    """Split a doc into passages by paragraph, capping length (simple but realistic)."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    chunks = []
    for p in paras:
        words = p.split()
        if len(words) <= max_words:
            chunks.append(p)
        else:
            for i in range(0, len(words), max_words):
                chunks.append(" ".join(words[i:i+max_words]))
    return chunks

class VectorStore:
    def __init__(self, embedder):
        self.embedder = embedder
        self.chunks: list[Chunk] = []
        self._bm25 = None

    @classmethod
    def build(cls, corpus_dir: str, embedder):
        from .loaders import load_documents
        vs = cls(embedder)
        for base, body, meta in load_documents(corpus_dir):   # .md / .pdf / .docx
            for i, ch in enumerate(_chunk_text(body)):
                vs.chunks.append(Chunk(f"{base}#{i}", ch, dict(meta)))
        texts = [c.text for c in vs.chunks]
        embedder.fit(texts)
        vecs = embedder.encode(texts)
        for c, v in zip(vs.chunks, vecs): c.vector = v
        # BM25 keyword index (hybrid search)
        try:
            from rank_bm25 import BM25Okapi
            vs._bm25 = BM25Okapi([t.lower().split() for t in texts])
        except Exception:
            vs._bm25 = None
        # optional cross-encoder reranker
        vs._reranker = None
        try:
            from sentence_transformers import CrossEncoder
            vs._reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        except Exception:
            pass
        return vs

    def _filter(self, where: dict | None):
        if not where: return list(range(len(self.chunks)))
        idx = []
        for i, c in enumerate(self.chunks):
            if all(str(c.metadata.get(k)) == str(v) for k, v in where.items()):
                idx.append(i)
        return idx or list(range(len(self.chunks)))  # fall back to all if filter empties

    def search(self, query: str, k=3, where: dict | None = None, candidates=12):
        cand = self._filter(where)
        qv = self.embedder.encode([query])[0]
        vec_scores = {i: float(np.dot(self.chunks[i].vector, qv)) for i in cand}
        # hybrid: blend normalised vector + BM25
        if self._bm25 is not None:
            bm = self._bm25.get_scores(query.lower().split())
            bm_max = max(bm[cand]) if len(cand) and max(bm[cand]) > 0 else 1.0
            scores = {i: 0.6*vec_scores[i] + 0.4*(bm[i]/bm_max) for i in cand}
        else:
            scores = vec_scores
        top = sorted(cand, key=lambda i: scores[i], reverse=True)[:candidates]
        # rerank: cross-encoder if available, else a lexical (BM25) rerank over the candidates
        if self._reranker is not None and top:
            pairs = [(query, self.chunks[i].text) for i in top]
            rr = self._reranker.predict(pairs)
            top = [i for _, i in sorted(zip(rr, top), reverse=True)]
        elif self._bm25 is not None and top:
            bm = self._bm25.get_scores(query.lower().split())
            top = sorted(top, key=lambda i: bm[i], reverse=True)
        out = []
        for i in top[:k]:
            c = self.chunks[i]; out.append(Chunk(c.chunk_id, c.text, c.metadata, score=scores[i]))
        return out
