"""Hybrid clause retrieval: BM25 keyword (SQLite FTS5) + local vectors, fused and re-ranked.

1. Keyword search catches exact technical terms ("C40/50", "bund", "BS 8500").
2. Vector search catches paraphrase ("oil containment" ≈ "bunding").
3. Reciprocal-rank fusion merges the two lists.
4. A lexical re-ranker rewards clauses that contain more of the query's terms,
   with extra weight on technical tokens (grades, numbers, standard references).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from . import embed, store
from .store import ClauseRow

STOPWORDS = set("""
a an and are as at be by can do does for from has have how i if in into is it its may me must my
no not of on or our shall should so such than that the their them then there these they this to
was we were what when where which who why will with would you your required requirement requirements
minimum maximum spec specification specifications clause clauses tell please give state say says
""".split())
FRONT_MATTER = {"issue record", "issue authority", "review", "distribution", "contents"}
TECH_TOKEN = re.compile(r"[A-Za-z]*\d[\w/.\-]*")
RRF_K = 60


@dataclass
class Hit:
    clause: ClauseRow
    score: float
    bm25_rank: int | None
    vector_rank: int | None
    coverage: float


def terms(query: str) -> list[str]:
    toks = re.findall(r"[A-Za-z0-9][A-Za-z0-9/]*(?:[.\-][A-Za-z0-9/]+)*", query)
    return [t for t in toks if t.lower() not in STOPWORDS and len(t) > 1]


def _fts_query(query: str) -> str:
    parts = []
    for t in terms(query):
        t = t.replace('"', "")
        # FTS splits "10.4" / "206-1" on punctuation; quote so the parts must be adjacent.
        parts.append(f'"{t}"')
    return " OR ".join(parts)


def _stem(w: str) -> str:
    w = w.lower()
    for suf in ("ings", "ing", "ies", "es", "s", "ed"):
        if len(w) > len(suf) + 3 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def coverage(query_terms: list[str], c: ClauseRow) -> float:
    if not query_terms:
        return 0.0
    hay = f"{c.heading} {c.text}".lower()
    hay_words = {_stem(w) for w in re.findall(r"[a-z0-9/]+", hay)}
    total = got = 0.0
    for t in query_terms:
        w = 2.0 if TECH_TOKEN.fullmatch(t) else 1.0
        total += w
        if t.lower() in hay or _stem(t) in hay_words:
            got += w
    return got / total


def allowed_ids(conn, doc_ids: list[str] | None) -> set[int] | None:
    if not doc_ids:
        return None
    q = f"SELECT id FROM clauses WHERE doc_id IN ({','.join('?' * len(doc_ids))})"
    return {r[0] for r in conn.execute(q, doc_ids)}


def keyword_search(conn, query: str, limit: int = 40, doc_ids: list[str] | None = None) -> list[int]:
    fq = _fts_query(query)
    if not fq:
        return []
    sql = ("SELECT f.rowid FROM clauses_fts f JOIN clauses c ON c.id = f.rowid "
           "WHERE clauses_fts MATCH ?")
    args: list = [fq]
    if doc_ids:
        sql += f" AND c.doc_id IN ({','.join('?' * len(doc_ids))})"
        args += doc_ids
    # Column weights: doc_id, clause_no, heading, path, text
    sql += " ORDER BY bm25(clauses_fts, 0, 1.0, 4.0, 1.5, 1.0) LIMIT ?"
    args.append(limit)
    return [r[0] for r in conn.execute(sql, args)]


def search(query: str, k: int = 10, doc_ids: list[str] | None = None, conn=None) -> list[Hit]:
    own = conn is None
    conn = conn or store.connect()
    try:
        allowed = allowed_ids(conn, doc_ids)
        kw = keyword_search(conn, query, 50, doc_ids)
        vec = [cid for cid, _ in embed.vector_search(query, 50, allowed)]
        fused: dict[int, float] = {}
        for ranked in (kw, vec):
            for r, cid in enumerate(ranked):
                fused[cid] = fused.get(cid, 0.0) + 1.0 / (RRF_K + r + 1)
        if not fused:
            return []
        candidates = sorted(fused, key=lambda c: -fused[c])[:60]
        rows = {c.id: c for c in store.get_clauses(conn, candidates)}
        qt = terms(query)
        top = max(fused.values())
        hits = []
        for cid in candidates:
            c = rows.get(cid)
            if c is None or len(c.text) < 20 or c.heading.lower() in FRONT_MATTER:
                continue
            cov = coverage(qt, c)
            score = 0.6 * (fused[cid] / top) + 0.4 * cov
            hits.append(Hit(c, score,
                            kw.index(cid) + 1 if cid in kw else None,
                            vec.index(cid) + 1 if cid in vec else None, cov))
        hits.sort(key=lambda h: -h.score)
        return hits[:k]
    finally:
        if own:
            conn.close()
