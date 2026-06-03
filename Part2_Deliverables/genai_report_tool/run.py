#!/usr/bin/env python3
"""Single entry point — the whole Part 2 pipeline in one command.

  python run.py                 # build stores -> generate Word+PDF report -> guardrail audit
  python run.py --eval          # also run the evaluation scorecard
  python run.py --backend mock  # offline (no API key); default backend is openai
  python run.py --embedder tfidf  # offline embeddings (default: sentence-transformers)

(ingest.py / generate_report.py / run_eval.py still exist for running a single stage.)
"""
import os, sys, argparse
sys.path.insert(0, os.path.dirname(__file__))
from src.env import load_env; load_env()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval", action="store_true", help="also run the evaluation scorecard")
    ap.add_argument("--backend", default=os.environ.get("LLM_BACKEND", "openai"),
                    choices=["openai", "anthropic", "azure", "mock"])
    ap.add_argument("--embedder", default=os.environ.get("EMBEDDER", "sentence-transformers"))
    args = ap.parse_args()
    os.environ["EMBEDDER"] = args.embedder

    from src.report_generator import generate_report
    from src.report_writer import render_docx, export_pdf
    from src.llm_client import OpenAIClient, AnthropicClient, AzureOpenAIClient, MockLLMClient
    llm = {"openai": OpenAIClient, "anthropic": AnthropicClient,
           "azure": AzureOpenAIClient, "mock": MockLLMClient}[args.backend]()

    print(f"[*] backend={args.backend}  embedder={args.embedder}")
    res = generate_report(llm=llm)
    outdir = os.path.join(os.path.dirname(__file__), "output"); os.makedirs(outdir, exist_ok=True)
    open(os.path.join(outdir, "valuation_report.md"), "w").write(res.report_md)
    docx = render_docx(res, os.path.join(outdir, "Valuation_Solvency_Report.docx"))
    pdf = export_pdf(docx)
    a = res.audit
    print(f"[*] corpus chunks indexed: {res.run_log['n_corpus_chunks']}")
    print("\n=== GUARDRAIL AUDIT ===")
    print(f"  input guardrail flags  : {a.input_guardrail_flags or 'none'}")
    print(f"  numeric reconciliation : {'PASS' if a.numeric_ok else 'FAIL '+str(a.unverified_numbers)}")
    print(f"  groundedness           : {'PASS' if not a.ungrounded_sections else 'FAIL'}")
    print(f"  template completeness  : {'PASS' if not a.missing_sections else 'FAIL'}")
    print(f"  OVERALL                : {'PASS -> ready for actuary review' if a.passed else 'BLOCKED'}")
    print("\n=== PROVENANCE (number -> source) ===")
    for r in res.provenance:
        print(f"  {r['number_in_report']:>18}  ->  {r['source']}  [{'OK' if r['ok'] else 'UNVERIFIED'}]")
    print(f"\n[*] Word: {docx}\n[*] PDF : {pdf or 'install MS Word or LibreOffice for PDF'}")

    if args.eval:
        from src.evaluation import evaluate
        e = evaluate(llm=llm)
        print("\n=== EVALUATION SCORECARD ===")
        print(f"  context recall    : {e['context_recall']}")
        print(f"  numeric pass-rate : {e['numeric_pass_rate']}  ({e['n_numbers_checked']} numbers)")
        print(f"  guardrails passed : {e['report_guardrails_passed']}")

if __name__ == "__main__":
    main()
