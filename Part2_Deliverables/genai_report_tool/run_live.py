#!/usr/bin/env python3
"""Live demo on the REAL OpenAI model: real run + a blocked hallucination."""
import os, sys, re; sys.path.insert(0, os.path.dirname(__file__))
from src.env import load_env; load_env()
from src.report_generator import generate_report
from src.llm_client import OpenAIClient
if "OPENAI_API_KEY" not in os.environ: sys.exit("Set OPENAI_API_KEY (e.g. in .env).")
class Tamper(OpenAIClient):
    def complete(self, system, prompt, context):
        t = super().complete(system, prompt, context)
        return re.sub(r"135(\.0)?%","152.4%",t) if context.get("section")=="Solvency (LICAT)" else t
print("=== REAL GPT run ===")
r = generate_report(llm=OpenAIClient()); print(r.report_md)
print("provenance:", [(x['number_in_report'],x['ok']) for x in r.provenance])
print(f"overall: {'PASS' if r.audit.passed else 'BLOCKED'}")
print("\n=== REAL GPT run with a corrupted figure (guardrail must BLOCK) ===")
r2 = generate_report(llm=Tamper())
print("unverified caught:", r2.audit.unverified_numbers, "| overall:", "PASS" if r2.audit.passed else "BLOCKED")
