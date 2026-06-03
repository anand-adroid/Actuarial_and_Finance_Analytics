"""LLM client abstraction.

Backends (all share the same .complete(system, prompt, context) -> body interface):
  * OpenAIClient      — direct OpenAI API (api.openai.com). LOCAL DEFAULT for running
                        the tool. Needs OPENAI_API_KEY. Install: pip install openai.
  * AnthropicClient   — direct Anthropic API (optional). Needs ANTHROPIC_API_KEY.
  * AzureOpenAIClient — Azure OpenAI (production path). Needs AZURE_OPENAI_* env vars.
  * MockLLMClient     — deterministic, offline. Used by the test suite so tests run
                        without an API key or network (and without spending tokens).

Each client returns ONLY the narrative body of a section. The orchestrator wraps the
heading and the verified citations around it, so formatting/citations are identical
regardless of which model is used.
"""
from __future__ import annotations
import os


class LLMClient:
    def complete(self, system: str, prompt: str, context: dict) -> str:
        raise NotImplementedError


class OpenAIClient(LLMClient):
    """Direct OpenAI (GPT). Set OPENAI_API_KEY; optionally OPENAI_MODEL (default gpt-4o)."""
    def __init__(self, model: str | None = None, temperature: float = 0.2):
        from openai import OpenAI  # lazy import so offline/mock use needs no openai package
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4o")
        self.temperature = temperature

    def complete(self, system: str, prompt: str, context: dict) -> str:
        resp = self.client.chat.completions.create(
            model=self.model, temperature=self.temperature,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content.strip()


class AnthropicClient(LLMClient):
    """Direct Anthropic (Claude). Set ANTHROPIC_API_KEY; optionally ANTHROPIC_MODEL."""
    def __init__(self, model: str | None = None, temperature: float = 0.2):
        import anthropic
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.model = model or os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
        self.temperature = temperature

    def complete(self, system: str, prompt: str, context: dict) -> str:
        resp = self.client.messages.create(
            model=self.model, max_tokens=800, temperature=self.temperature,
            system=system, messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text.strip()


class AzureOpenAIClient(LLMClient):
    """Azure OpenAI (production). Needs AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_DEPLOYMENT."""
    def __init__(self, temperature: float = 0.2):
        from openai import AzureOpenAI
        self.deployment = os.environ["AZURE_OPENAI_DEPLOYMENT"]
        self.client = AzureOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-06-01"),
        )
        self.temperature = temperature

    def complete(self, system: str, prompt: str, context: dict) -> str:
        resp = self.client.chat.completions.create(
            model=self.deployment, temperature=self.temperature,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content.strip()


class MockLLMClient(LLMClient):
    """Deterministic, offline stand-in used by the tests. Fills the section template
    with the verified figures (so output is grounded and reconcilable) — no network."""
    def complete(self, system: str, prompt: str, context: dict) -> str:
        body = context.get("template", "")
        for k, v in context.get("facts", {}).items():
            body = body.replace("{{" + k + "}}", str(v))
        return body.strip()
