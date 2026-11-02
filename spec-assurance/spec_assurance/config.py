"""Paths and settings, read once from the environment / .env file."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv() -> None:
    """Minimal .env reader so the app has no extra dependency for it."""
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()

LIBRARY_DIR = Path(os.environ.get("SA_LIBRARY_DIR", ROOT / "library"))
DATA_DIR = Path(os.environ.get("SA_DATA_DIR", ROOT / "data"))
DB_PATH = DATA_DIR / "spec_assurance.db"
VECTORS_PATH = DATA_DIR / "vectors.npz"
EMBED_MODEL_DIR = Path(os.environ.get("SA_EMBED_MODEL_DIR", ROOT / "models" / "potion-base-8M"))
HIERARCHY_PATH = ROOT / "hierarchy.json"

CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")
CLAUDE_EFFORT = os.environ.get("CLAUDE_EFFORT", "medium")
# "mock" runs the whole app offline with a deterministic stand-in for Claude.
LLM_MODE = os.environ.get("SA_LLM_MODE", "auto")  # auto | live | mock

TESSERACT_CMD = os.environ.get("TESSERACT_CMD", "")

DATA_DIR.mkdir(parents=True, exist_ok=True)
LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
