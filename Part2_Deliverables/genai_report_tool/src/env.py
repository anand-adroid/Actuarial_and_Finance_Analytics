"""Load environment variables from a local .env file if present.

Uses python-dotenv when installed; otherwise falls back to a tiny built-in parser so
the tool still works without the dependency. Call load_env() once at program start.
"""
from __future__ import annotations
import os

def load_env(path: str | None = None) -> None:
    here = os.path.dirname(os.path.dirname(__file__))   # tool root
    env_path = path or os.path.join(here, ".env")
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
        return
    except Exception:
        pass
    # fallback: minimal parser (KEY=VALUE lines)
    if os.path.exists(env_path):
        for line in open(env_path):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
