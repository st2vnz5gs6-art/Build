"""Local semantic index.

Embeddings come from a small static model (model2vec "potion-base-8M", ~30 MB)
shipped in /models, so nothing is downloaded at install time and no document
text leaves the machine. Long clauses are embedded as overlapping windows; a
clause scores as its best-matching window.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np

from . import config
from .store import ClauseRow

WINDOW_WORDS = 140
OVERLAP_WORDS = 40


@lru_cache(maxsize=1)
def model():
    from model2vec import StaticModel

    return StaticModel.from_pretrained(str(config.EMBED_MODEL_DIR))


def encode(texts: list[str]) -> np.ndarray:
    if not texts:
        return np.zeros((0, 256), dtype=np.float32)
    v = np.asarray(model().encode(texts), dtype=np.float32)
    v /= np.linalg.norm(v, axis=1, keepdims=True) + 1e-9
    return v


def _windows(c: ClauseRow) -> list[str]:
    prefix = f"{c.path} › {c.clause_no} {c.heading}: " if c.path else f"{c.clause_no} {c.heading}: "
    words = c.text.split()
    if len(words) <= WINDOW_WORDS:
        return [prefix + c.text]
    out, step = [], WINDOW_WORDS - OVERLAP_WORDS
    for start in range(0, len(words), step):
        out.append(prefix + " ".join(words[start:start + WINDOW_WORDS]))
        if start + WINDOW_WORDS >= len(words):
            break
    return out


def build_index(clauses: list[ClauseRow]) -> None:
    texts, owners = [], []
    for c in clauses:
        if len(c.text) < 20:
            continue
        for w in _windows(c):
            texts.append(w)
            owners.append(c.id)
    vecs = encode(texts)
    np.savez_compressed(config.VECTORS_PATH, vectors=vecs, clause_ids=np.asarray(owners, dtype=np.int64))
    load_index.cache_clear()


@lru_cache(maxsize=1)
def load_index() -> tuple[np.ndarray, np.ndarray]:
    if not config.VECTORS_PATH.exists():
        return np.zeros((0, 256), dtype=np.float32), np.zeros(0, dtype=np.int64)
    data = np.load(config.VECTORS_PATH)
    return data["vectors"], data["clause_ids"]


def vector_search(query: str, limit: int = 40, allowed: set[int] | None = None) -> list[tuple[int, float]]:
    vecs, owners = load_index()
    if len(owners) == 0:
        return []
    sims = vecs @ encode([query])[0]
    best: dict[int, float] = {}
    for idx in np.argsort(-sims):
        cid = int(owners[idx])
        if allowed is not None and cid not in allowed:
            continue
        if cid not in best:
            best[cid] = float(sims[idx])
            if len(best) >= limit:
                break
    return sorted(best.items(), key=lambda kv: -kv[1])
