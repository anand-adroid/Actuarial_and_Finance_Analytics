"""Ingestion pipeline: build the two stores from the labelled inputs + corpus.

Simulates the production ETL: numbers -> SQLite; documents -> chunk/embed/index.
"""
from __future__ import annotations
import os
from .structured_store import StructuredStore
from .vector_store import VectorStore
from .embeddings import get_embedder

ROOT = os.path.dirname(os.path.dirname(__file__))
INPUTS = os.path.join(ROOT, "data", "inputs")
CORPUS = os.environ.get("GENAI_CORPUS_DIR", os.path.join(ROOT, "data", "corpus"))
BUILD = os.environ.get("GENAI_BUILD_DIR", os.path.join(ROOT, "build"))

def build_stores(embedder_name: str | None = None):
    os.makedirs(BUILD, exist_ok=True)
    store = StructuredStore.build(os.path.join(BUILD, "valuation.db"), {
        "model_outputs":        os.path.join(INPUTS, "model_outputs.csv"),
        "financial_statements": os.path.join(INPUTS, "financial_statements.csv"),
        "macro":                os.path.join(INPUTS, "macro.csv"),
    })
    embedder = get_embedder(embedder_name)
    corpus = os.environ.get("GENAI_CORPUS_DIR", CORPUS)
    vstore = VectorStore.build(corpus, embedder)
    return store, vstore, embedder
