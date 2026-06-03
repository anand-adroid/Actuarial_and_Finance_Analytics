"""Evaluation harness (offline). Computes RAG + factuality metrics against a golden set.

  * context precision/recall : did retrieval return the EXPECTED source doc for each section?
  * numeric pass-rate        : fraction of report numbers that reconcile to the source of truth.
  * faithfulness (LLM-judge) : OPTIONAL — if a real LLM is supplied, score each section 0/1
                               for being supported by its figures (skipped for MockLLM).
"""
from __future__ import annotations
from .ingestion import build_stores
from .retriever import Retriever
from .orchestrator import Orchestrator, SECTIONS
from .report_generator import generate_report, _provenance_table
from .llm_client import MockLLMClient

# golden set: which source doc SHOULD be retrieved for each section query
GOLDEN_SOURCES = {
    "Executive Summary": {"PRIOR_REPORT"},
    "Portfolio Overview": {"INTERNAL_POLICY", "IFRS17"},
    "Reserving Position": {"IFRS17", "INTERNAL_POLICY"},
    "Solvency (LICAT)": {"OSFI_LICAT"},
    "Macroeconomic Sensitivity": {"INTERNAL_POLICY"},
}

def evaluate(llm=None, embedder_name=None):
    store, vstore, emb = build_stores(embedder_name)
    retr = Retriever(vstore)
    ctx_hits, ctx_total = 0, 0
    per_section = []
    for title, query, where, metrics, template in SECTIONS:
        got = {c.metadata.get("source") for c in retr.retrieve(query, k=2, where=where)}
        want = GOLDEN_SOURCES.get(title, set())
        hit = bool(got & want)
        ctx_hits += int(hit); ctx_total += 1
        per_section.append({"section": title, "retrieved": sorted(got), "expected": sorted(want), "hit": hit})
    context_recall = ctx_hits / ctx_total

    res = generate_report(llm=llm or MockLLMClient(), stores=(store, vstore, emb))
    prov = res.provenance
    numeric_pass = sum(r["ok"] for r in prov) / max(len(prov), 1)
    return {
        "context_recall": round(context_recall, 3),
        "numeric_pass_rate": round(numeric_pass, 3),
        "report_guardrails_passed": res.audit.passed,
        "per_section_retrieval": per_section,
        "n_numbers_checked": len(prov),
    }
