"""Thin RAG interface over the vector store (metadata filter -> hybrid -> rerank)."""
from __future__ import annotations
class Retriever:
    def __init__(self, vstore):
        self.vstore = vstore
    def retrieve(self, query: str, k=3, where: dict | None = None):
        return self.vstore.search(query, k=k, where=where)
