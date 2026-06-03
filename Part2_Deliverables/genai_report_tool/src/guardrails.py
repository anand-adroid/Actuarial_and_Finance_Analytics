"""Guardrails — INPUT (before the LLM) and OUTPUT (before a human).

INPUT  : PII redaction + prompt-injection screening of retrieved/untrusted text.
OUTPUT : numeric reconciliation, groundedness, template completeness.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field

# ---------- INPUT GUARDRAILS ----------
PII_PATTERNS = {
    "EMAIL": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "POLICY_ID": re.compile(r"\bP-\d{4,}\b"),
    "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "PHONE": re.compile(r"\b\d{3}[-.]\d{3}[-.]\d{4}\b"),
}
# heuristic prompt-injection signatures (OWASP LLM01). Production: a dedicated classifier.
INJECTION_PATTERNS = [
    r"ignore (all |the )?(previous|above|prior) (instructions|prompt)",
    r"disregard (the |all )?(system|previous) (prompt|instructions)",
    r"you are now", r"reveal (the )?(system|hidden) prompt",
    r"act as", r"override (the )?(rules|guardrails)",
]
_INJ = re.compile("|".join(INJECTION_PATTERNS), re.IGNORECASE)

def redact_pii(text: str):
    found = []
    for label, pat in PII_PATTERNS.items():
        if pat.search(text):
            found.append(label); text = pat.sub(f"[REDACTED_{label}]", text)
    return text, found

def screen_injection(text: str) -> bool:
    """True if the (untrusted) text contains a likely prompt-injection attempt."""
    return bool(_INJ.search(text))

def sanitize_context(text: str):
    """Run input guardrails on a retrieved chunk before it enters the prompt."""
    clean, pii = redact_pii(text)
    injected = screen_injection(clean)
    if injected:                    # neutralise rather than pass through
        clean = "[BLOCKED: untrusted instruction removed]"
    return clean, {"pii": pii, "injection": injected}

# ---------- OUTPUT GUARDRAILS ----------
NUM_RE = re.compile(r"-?\$?\d[\d,]*\.?\d*%?")
def _to_float(tok):
    t = tok.replace("$","").replace(",","").replace("%","")
    try: return round(float(t),2)
    except ValueError: return None

@dataclass
class ReconResult:
    ok: bool
    unverified: list = field(default_factory=list)

def reconcile_numbers(draft, verified, ignore_small_ints=True):
    bad=[]
    for tok in NUM_RE.findall(draft):
        val=_to_float(tok)
        if val is None: continue
        if ignore_small_ints and val.is_integer() and abs(val)<100: continue
        if not any(abs(val-v)<=max(0.01,abs(v)*0.005) for v in verified): bad.append(tok)
    return ReconResult(len(bad)==0, bad)

def check_groundedness(section_text):
    return "_Sources:" in section_text and "n/a" not in section_text.split("_Sources:")[-1]

def check_template(report, required):
    return [s for s in required if s not in report]
