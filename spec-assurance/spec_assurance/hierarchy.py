"""Configurable precedence between documents (hierarchy.json)."""

from __future__ import annotations

import json
import re
from functools import lru_cache

from . import config


@lru_cache(maxsize=1)
def load() -> dict:
    return json.loads(config.HIERARCHY_PATH.read_text(encoding="utf-8"))


def tier_for(doc_id: str) -> str:
    h = load()
    for rule in h["rules"]:
        if re.search(rule["pattern"], doc_id, re.I):
            return rule["tier"]
    return h["default_tier"]


def rank(tier: str) -> int:
    tiers = load()["tiers"]
    return tiers.index(tier) if tier in tiers else len(tiers)


def precedence_text() -> str:
    return " > ".join(load()["tiers"])


def scope_presets() -> dict[str, list[str]]:
    return load()["scope_presets"]
