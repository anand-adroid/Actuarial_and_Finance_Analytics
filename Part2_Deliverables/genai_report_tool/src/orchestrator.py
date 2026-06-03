"""Section-by-section orchestration (the harness).

Per section: fetch exact numbers (SQL) + retrieve text (RAG with metadata filter) ->
run INPUT guardrails on retrieved text -> build grounded prompt -> LLM -> wrap heading+citations.
"""
from __future__ import annotations
from dataclasses import dataclass
from . import guardrails as G

SYSTEM = ("You are an actuarial report writer for a regulated insurer. Write only from the "
          "VERIFIED FIGURES supplied, quoting each number EXACTLY as given (never round or invent). "
          "Use the reference context only for wording. Output 2-4 sentences of professional prose, "
          "no heading, no sources line.")

# (title, retrieval query, metadata filter, metrics, fallback template for MockLLM)
SECTIONS = [
 ("Executive Summary","executive summary solvency overview",{"topic":"overview"},
  ["licat_ratio_pct","policy_reserves_usd","portfolio_policy_count"],
  "For the {{valuation_period}} valuation, the long-term-care portfolio of {{portfolio_policy_count}} "
  "policies holds reserves of {{policy_reserves_usd}} and reports a LICAT ratio of {{licat_ratio_pct}}, "
  "above the 100% supervisory target."),
 ("Portfolio Overview","portfolio claim frequency expected loss pricing",{"topic":"reserving"},
  ["portfolio_policy_count","portfolio_claim_frequency","portfolio_mean_expected_loss_usd","gross_written_premium_usd"],
  "The portfolio comprises {{portfolio_policy_count}} policies with a claim frequency of "
  "{{portfolio_claim_frequency}}. Mean expected loss per policy is {{portfolio_mean_expected_loss_usd}}, "
  "supporting gross written premium of {{gross_written_premium_usd}}."),
 ("Reserving Position","reserving policy IFRS 17 fulfilment cash flows",{"topic":"reserving"},
  ["policy_reserves_usd","portfolio_total_expected_claims_usd"],
  "Policy reserves stand at {{policy_reserves_usd}}, covering total expected claims of "
  "{{portfolio_total_expected_claims_usd}}. Reserves follow prescribed actuarial standards, not the pricing model."),
 ("Solvency (LICAT)","LICAT available required capital supervisory target",{"topic":"solvency"},
  ["available_capital_usd","required_capital_usd","licat_ratio_pct"],
  "Available capital of {{available_capital_usd}} against required capital of {{required_capital_usd}} "
  "yields a LICAT ratio of {{licat_ratio_pct}}, indicating capital adequacy under adverse scenarios."),
 ("Macroeconomic Sensitivity","macroeconomic inflation discount rate sensitivity",{"topic":"macroeconomic"},
  ["macro_inflation_rate_pct","discount_rate_pct","wage_inflation_pct"],
  "Key assumptions: inflation {{macro_inflation_rate_pct}}, discount rate {{discount_rate_pct}}, "
  "wage inflation {{wage_inflation_pct}}. Reserves are sensitive to inflation and discount-rate moves."),
]

@dataclass
class SectionResult:
    title: str; text: str; sources: list; grounded: bool; input_flags: list; retrieved: list

class Orchestrator:
    def __init__(self, store, retriever, llm):
        self.store, self.retriever, self.llm = store, retriever, llm

    def build_section(self, title, query, where, metrics, template):
        facts = {m: self.store.fmt(m) for m in metrics}
        facts.setdefault("valuation_period", self.store.fmt("valuation_period"))
        chunks = self.retriever.retrieve(query, k=2, where=where)
        retrieved = [{"chunk_id": c.chunk_id, "source": c.metadata.get("source"),
                      "score": round(float(c.score),3),
                      "snippet": " ".join(c.text.split())[:140]} for c in chunks]
        # INPUT GUARDRAILS on each retrieved (untrusted) chunk before it enters the prompt
        clean_ctx, flags = [], []
        for c in chunks:
            txt, f = G.sanitize_context(c.text); clean_ctx.append(f"[{c.metadata.get('source')}] {txt}")
            if f["pii"] or f["injection"]: flags.append({"chunk": c.chunk_id, **f})
        facts_text = "\n".join(f"- {k} = {v}" for k, v in facts.items())
        prompt = (f"Write the '{title}' section of an Actuarial Valuation & Solvency Report.\n\n"
                  f"VERIFIED FIGURES (use ONLY these, quote EXACTLY):\n{facts_text}\n\n"
                  f"REFERENCE CONTEXT (wording only, no numbers):\n" + "\n".join(clean_ctx) + "\n\n"
                  f"Write 2-4 sentences. No heading, no sources line.")
        ctx = {"facts": facts, "sources": [c.metadata.get("source") for c in chunks],
               "section": title, "template": template}
        body = self.llm.complete(SYSTEM, prompt, ctx).strip()
        cites = ", ".join(ctx["sources"]) or "n/a"
        text = f"## {title}\n{body}\n\n_Sources: {cites}_"
        return SectionResult(title, text, ctx["sources"], G.check_groundedness(text), flags, retrieved)

    def build_all(self):
        return [self.build_section(*spec) for spec in SECTIONS]
