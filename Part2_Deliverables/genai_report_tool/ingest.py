#!/usr/bin/env python3
"""Build the two stores (SQLite + vector index) from data/inputs and data/corpus."""
import os, sys; sys.path.insert(0, os.path.dirname(__file__))
from src.env import load_env; load_env()
from src.ingestion import build_stores
store, vstore, emb = build_stores()
print(f"[*] Structured store: {len(store.conn.execute('SELECT * FROM metrics').fetchall())} metrics loaded")
print(f"[*] Vector store: {len(vstore.chunks)} chunks embedded with '{emb.name}'")
print("[*] Stores built under build/.")
