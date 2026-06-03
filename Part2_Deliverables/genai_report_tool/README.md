# Automated Actuarial Valuation & Solvency Report — GenAI POC (Part 2)

A full, runnable proof-of-concept of the Part 2 architecture. It ingests three labelled
data inputs plus a governed document corpus (PDF / Word / Markdown), retrieves the right
context with RAG, drafts the report with an LLM, enforces input + output guardrails, and
renders a **branded Word + PDF report** with formatted tables and inline citations — proving
every number traces back to a verified source.

**Core principle:** the LLM composes the narrative; it never invents a number. Numbers come
from a structured store by exact SQL; documents come from a vector store by RAG.

## Two stores
| Store | Holds | Queried by | Production equivalent |
|-------|-------|-----------|------------------------|
| Structured (`build/valuation.db`, SQLite) | the NUMBERS | deterministic templated SQL | Azure SQL / Synapse / Fabric |
| Vector (in-memory) | the DOCUMENTS (PDF/Word/MD, chunked + embedded + metadata) | metadata filter → hybrid (vector+BM25) → cross-encoder rerank | Azure AI Search |

## Inputs
- `data/inputs/model_outputs.csv` — Part 1 model outputs (exported by the Part 1 notebook).
- `data/inputs/financial_statements.csv` — GL / reserve / capital figures.
- `data/inputs/macro.csv` — macroeconomic assumptions.
- `data/corpus/` — governed documents in **.md, .pdf and .docx** (with tables); non-markdown
  files get metadata from `_manifest.csv` (simulates a document-management catalogue).

## Setup
```bash
python -m venv .venv && . .venv/bin/activate     # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env        # put your OPENAI_API_KEY in .env
```
First run downloads the local embedding + reranker models (sentence-transformers), one time.

## Run (real OpenAI by default)
```bash
python ingest.py             # parse corpus (PDF/Word/MD) + build the two stores
python generate_report.py    # draft -> guardrails -> PROVENANCE table -> Word + PDF
python run_eval.py           # evaluation scorecard (context recall, numeric pass-rate)
python run_live.py           # live demo: real run + a blocked hallucination
```
Outputs in `output/`: `Valuation_Solvency_Report.docx` + `.pdf`, `valuation_report.md`,
and `run_log.json` (audit trail). PDF export needs MS Word (`docx2pdf`) or LibreOffice.

## Backends / embedders (env or .env)
- `LLM_BACKEND` = `openai` (default) | `anthropic` | `azure` | `mock`
- `EMBEDDER`    = `sentence-transformers` (default) | `openai` | `tfidf`

## Test (offline — no key, no torch, no tokens)
```bash
EMBEDDER=tfidf python -m pytest -q
```
Covers: input guardrails (PII + injection), numeric reconciliation, **multi-format ingestion
(md+pdf+docx)**, metadata-filtered retrieval, end-to-end provenance + citations + tables, the
Word renderer, and the evaluation harness.

## POC vs production
Real algorithms throughout (two stores, embeddings, hybrid+rerank, multi-format parsing,
guardrails, eval, Word/PDF rendering, audit log). To productionise: structured store on Azure
SQL/Fabric; vectors on Azure AI Search (with security-trimming + versioning); parsing via Azure
AI Document Intelligence; model on Azure OpenAI (private VNet); orchestrate with Prompt Flow;
guardrails via Azure AI Content Safety + Presidio; eval in CI; Azure Monitor observability;
publish to SharePoint/DMS — all wrapped in Entra ID RBAC, Key Vault, Purview and audit logging.
