#!/usr/bin/env python3
"""Run the evaluation harness and print a scorecard."""
import os, sys, json; sys.path.insert(0, os.path.dirname(__file__))
from src.env import load_env; load_env()
from src.evaluation import evaluate
from src.llm_client import OpenAIClient, MockLLMClient
backend = os.environ.get("LLM_BACKEND","mock").lower()
llm = OpenAIClient() if backend=="openai" else MockLLMClient()
r = evaluate(llm=llm)
print("=== EVALUATION SCORECARD ===")
print(f"  context recall (right docs retrieved): {r['context_recall']}")
print(f"  numeric pass-rate (numbers reconciled): {r['numeric_pass_rate']}  ({r['n_numbers_checked']} numbers)")
print(f"  report passed all guardrails         : {r['report_guardrails_passed']}")
print("\n  per-section retrieval:")
for s in r["per_section_retrieval"]:
    print(f"    {s['section']:<26} hit={s['hit']}  got={s['retrieved']}  want={s['expected']}")
