#!/usr/bin/env python3
"""Generate the report (Word + PDF). DEFAULT backend = real OpenAI (set OPENAI_API_KEY in .env)."""
import os, sys; sys.path.insert(0, os.path.dirname(__file__))
from src.env import load_env; load_env()
from src.report_generator import generate_report
from src.report_writer import render_docx, export_pdf
from src.llm_client import OpenAIClient, AnthropicClient, AzureOpenAIClient, MockLLMClient
def make_llm(b): return {"openai":OpenAIClient,"anthropic":AnthropicClient,"azure":AzureOpenAIClient,"mock":MockLLMClient}[b]()
backend = os.environ.get("LLM_BACKEND","openai").lower()
print(f"[*] LLM backend: {backend} | embedder: {os.environ.get('EMBEDDER','sentence-transformers')}")
res = generate_report(llm=make_llm(backend))
outdir = os.path.join(os.path.dirname(__file__),"output")
open(os.path.join(outdir,"valuation_report.md"),"w").write(res.report_md)
docx_path = render_docx(res, os.path.join(outdir,"Valuation_Solvency_Report.docx"))
pdf_path = export_pdf(docx_path)
a = res.audit
print(f"[*] corpus chunks indexed: {res.run_log['n_corpus_chunks']}")
print("\n=== GUARDRAIL AUDIT ===")
print(f"  input guardrail flags  : {a.input_guardrail_flags or 'none'}")
print(f"  numeric reconciliation : {'PASS' if a.numeric_ok else 'FAIL '+str(a.unverified_numbers)}")
print(f"  groundedness           : {'PASS' if not a.ungrounded_sections else 'FAIL '+str(a.ungrounded_sections)}")
print(f"  template completeness  : {'PASS' if not a.missing_sections else 'FAIL '+str(a.missing_sections)}")
print(f"  OVERALL                : {'PASS -> ready for actuary review' if a.passed else 'BLOCKED'}")
print("\n=== PROVENANCE (every number vs its source) ===")
for r in res.provenance:
    print(f"  {r['number_in_report']:>18}  ->  {r['source']}  [{'OK' if r['ok'] else 'UNVERIFIED'}]")
print(f"\n[*] Word: {docx_path}")
print(f"[*] PDF : {pdf_path or 'not generated (install MS Word or LibreOffice)'}")
print(f"[*] Audit log: output/run_log.json")
