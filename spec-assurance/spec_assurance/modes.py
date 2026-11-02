"""The three modes: Ask, RFI and Document review.

Each mode retrieves clauses, asks Claude for a structured answer (or, with no
API key, builds an extractive offline answer), verifies every citation, logs
the result and returns a plain dataclass the UI and exporters render.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import config, llm, search, store
from .citations import Rejection, Verified, Verifier, normalise
from .ingest import drawings
from .search import Hit, terms

TECH = re.compile(r"\b(?:C\d{2}/\d{2}|\d+(?:\.\d+)?\s?(?:mm|m|kN|kPa|MPa|%|l|litres|kV|°)|BS\s?(?:EN\s?)?\d+|S\d{3}|B500[ABC]?|XC\d|XD\d|XS\d|XF\d|grade\s+\w+)", re.I)
REQ_WORDS = re.compile(r"\b(shall|must|should|minimum|maximum|not less than|not exceed|at least|required|grade|class|cover|thick|capacity|load|galvani[sz]|coating|exposure)\b", re.I)
DRAWING_HINT = re.compile(r"\b(drawing\s*(no|number)|drg\.?\s*no|title\s*block|scale\s*1\s*:|general\s+notes|do not scale|sheet\s+\d+\s+of)\b", re.I)


@dataclass
class Answer:
    mode: str
    query: str
    offline: bool
    model: str
    coverage: str
    answer: str
    quotes: list[Verified]
    interpretation: str
    gaps_conflicts: list[str]
    likely_standard: str
    hits: list[Hit]
    rejected: list[Rejection]
    # RFI only
    position: str = ""
    position_basis: str = ""
    rfi_summary: str = ""
    draft_response: str = ""
    error: str = ""
    cited: list[str] = field(default_factory=list)

    def as_log(self) -> dict:
        return {
            "answer": self.answer, "coverage": self.coverage, "position": self.position,
            "position_basis": self.position_basis, "draft_response": self.draft_response,
            "interpretation": self.interpretation, "gaps_conflicts": self.gaps_conflicts,
            "likely_standard": self.likely_standard,
            "quotes": [{"citation": q.clause.citation, "quote": q.quote} for q in self.quotes],
            "retrieved": [h.clause.citation for h in self.hits], "error": self.error,
        }


def _missing_terms(query: str, hits: list[Hit]) -> list[str]:
    """Technical tokens in the query that no retrieved clause contains (e.g. 'C40/50')."""
    hay = normalise(" ".join(h.clause.text for h in hits))
    return [t for t in terms(query) if re.search(r"\d", t) and t.lower() not in hay]


def _sentences(text: str) -> list[str]:
    flat = re.sub(r"\s+", " ", text.replace("[Table]", " "))
    return [s.strip() for s in re.split(r"(?<=[.;:])\s+(?=[A-Z•(])", flat) if len(s.strip()) > 25]


def _best_sentences(query: str, hit: Hit, n: int = 2) -> list[str]:
    qt = [search._stem(t) for t in terms(query)]
    scored = []
    for s in _sentences(hit.clause.text):
        words = {search._stem(w) for w in re.findall(r"[A-Za-z0-9/]+", s)}
        score = sum(1 for t in qt if t in words) + (0.5 if REQ_WORDS.search(s) else 0)
        scored.append((score, s))
    scored.sort(key=lambda x: -x[0])
    return [s for sc, s in scored[:n] if sc > 0]


def _finish(conn, ans: Answer) -> Answer:
    store.log_query(conn, ans.mode, ans.query, ans.as_log(), ans.cited,
                    [r.detail for r in ans.rejected], ans.model)
    return ans


def _offline_answer(mode: str, query: str, hits: list[Hit], conn) -> Answer:
    v = Verifier([h.clause for h in hits], conn)
    for i, h in enumerate(hits[:3], 1):
        for s in _best_sentences(query, h):
            v.quote(f"C{i}", s)
    missing = _missing_terms(query, hits)
    gaps = [f"“{t}” does not appear in any retrieved clause." for t in missing]
    gaps.insert(0, "Offline mode: no Claude API key configured. The passages below are the closest matching clause text, "
                   "selected by search only — they have not been interpreted. Add ANTHROPIC_API_KEY to .env for assessed answers.")
    return Answer(
        mode=mode, query=query, offline=True, model="offline-extractive",
        coverage="partial" if v.result.quotes else "not_covered",
        answer="Closest matching requirements are quoted below for manual review." if v.result.quotes
        else "Not covered by the library.",
        quotes=v.result.quotes, interpretation="", gaps_conflicts=gaps, likely_standard="",
        hits=hits, rejected=v.result.rejected,
        position="Clarification needed" if mode == "rfi" else "",
        position_basis="Offline mode — position not assessed." if mode == "rfi" else "",
        cited=v.result.cited_list,
    )


def _not_covered(mode: str, query: str, conn) -> Answer:
    return Answer(mode, query, llm.mode() != "live", config.CLAUDE_MODEL, "not_covered",
                  "Not covered by the library: no clause matched this query.", [], "",
                  ["No clause in the selected documents matched the search."], "", [], [],
                  position="Clarification needed" if mode == "rfi" else "")


def ask(question: str, doc_ids: list[str] | None = None, k: int = 10) -> Answer:
    return _qa("ask", question, doc_ids, k)


def rfi(rfi_text: str, doc_ids: list[str] | None = None, k: int = 12) -> Answer:
    return _qa("rfi", rfi_text, doc_ids, k)


def _qa(mode: str, query: str, doc_ids: list[str] | None, k: int) -> Answer:
    with store.session() as conn:
        hits = search.search(query, k, doc_ids, conn)
        if not hits:
            return _finish(conn, _not_covered(mode, query, conn))
        if llm.mode() != "live":
            return _finish(conn, _offline_answer(mode, query, hits, conn))

        clauses = [h.clause for h in hits]
        missing = _missing_terms(query, hits)
        note = (f"\n\nNote: these terms from the query appear in none of the clauses: {', '.join(missing)}." if missing else "")
        task = ("Answer the question using only the clauses above." if mode == "ask" else
                "Assess this RFI against the clauses above. Give the compliance position (Compliant / Non-compliant / "
                "Clarification needed) of what the RFI proposes or asks, and draft a response for issue to the contractor.")
        prompt = f"<clauses>\n{llm.format_clauses(clauses)}\n</clauses>\n\n<{mode}>\n{query}\n</{mode}>{note}\n\n{task}"
        try:
            out = llm.call(llm.AskAnswer if mode == "ask" else llm.RFIAnswer, prompt)
        except llm.LLMUnavailable as exc:
            ans = _offline_answer(mode, query, hits, conn)
            ans.error = str(exc)
            ans.gaps_conflicts[0] = f"Claude unavailable ({exc}). Showing search results only."
            return _finish(conn, ans)

        v = Verifier(clauses, conn)
        for q in out.spec_says:
            v.quote(q.ref, q.quote)
        ans = Answer(
            mode=mode, query=query, offline=False, model=config.CLAUDE_MODEL, coverage=out.coverage,
            answer=v.text(out.answer if mode == "ask" else out.rfi_summary),
            quotes=v.result.quotes, interpretation=v.text(out.interpretation),
            gaps_conflicts=[v.text(g) for g in out.gaps_conflicts] + [f"“{t}” does not appear in any retrieved clause." for t in missing if not any(t in g for g in out.gaps_conflicts)],
            likely_standard=out.likely_standard, hits=hits, rejected=v.result.rejected,
        )
        if mode == "rfi":
            ans.position = out.position
            ans.position_basis = v.text(out.position_basis)
            ans.rfi_summary = ans.answer
            ans.draft_response = v.text(out.draft_response)
        ans.cited = v.result.cited_list
        if ans.coverage != "not_covered" and not ans.quotes:
            ans.coverage = "partial"
            ans.gaps_conflicts.append("No quote could be verified against the library, so this answer is unsupported — check the retrieved clauses directly.")
        return _finish(conn, ans)


# --------------------------------------------------------------------------- document review

@dataclass
class ReviewRow:
    no: int
    location: str
    statement: str
    citations: list[str]
    quote: str
    finding: str
    rag: str
    comment: str
    quote_verified: bool
    candidates: list[str] = field(default_factory=list)


@dataclass
class MissingRow:
    requirement: str
    citation: str
    quote: str
    status: str


@dataclass
class Review:
    filename: str
    offline: bool
    model: str
    document_kind: str
    title_block: str
    pages: list[drawings.PageText]
    rows: list[ReviewRow]
    missing: list[MissingRow]
    rejected: list[Rejection]
    error: str = ""

    @property
    def rag_counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for r in self.rows:
            out[r.rag] = out.get(r.rag, 0) + 1
        return out


ITEM_START = re.compile(r"^\s*(?:note\s*)?(\d{1,3}(?:\.\d{1,2}){0,3})[.)]?\s+(?=\S)", re.I)


def _items(text: str) -> list[tuple[str | None, str]]:
    """Group lines into numbered items (wrapped drawing notes, numbered paragraphs)."""
    items: list[list] = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        m = ITEM_START.match(s)
        if m or not items or items[-1][1].rstrip().endswith((".", ":", ";")):
            items.append([m.group(1) if m else None, s[m.end():] if m else s])
        else:
            items[-1][1] += " " + s
    return [(n, re.sub(r"\s+", " ", t)) for n, t in items]


def heuristic_statements(pages: list[drawings.PageText], drawing: bool = False, max_items: int = 60) -> list[llm.ExtractedStatement]:
    """Offline statement extraction: numbered items/sentences carrying a technical value or requirement."""
    out = []
    for p in pages:
        for number, item in _items(p.text):
            for s in (re.split(r"(?<=[.;])\s+(?=[A-Z])", item) if len(item) > 300 else [item]):
                if len(s) < 20 or not (TECH.search(s) or REQ_WORDS.search(s)):
                    continue
                loc = (f"note {number}" if drawing else f"§{number}") if number else ""
                if p.page and len(pages) > 1:
                    loc = f"p.{p.page}" + (f", {loc}" if loc else "")
                out.append(llm.ExtractedStatement(location=loc or "—", statement=s[:600], topic=" ".join(terms(s)[:8])))
                if len(out) >= max_items:
                    return out
    return out


def _extract_live(name: str, pages: list[drawings.PageText]) -> llm.Extraction:
    body = "\n\n".join(f"<page n=\"{p.page}\" method=\"{p.method}\">\n{p.text}\n</page>" for p in pages)
    prompt = (
        f"<document name=\"{name}\">\n{body}\n</document>\n\n"
        "Extract every technical statement in this document that can be checked against a civil/structural "
        "specification: material grades and classes, exposure classes, concrete cover, reinforcement and steel grades, "
        "bolt grades, galvanising and coatings, dimensions and thicknesses, capacities, design loads and load cases, "
        "drainage and flood criteria, fire separation, referenced standards, and statements of compliance. "
        "For a drawing include every general/specific note (with its note number) and the title block. "
        "Copy each statement as written. Ignore geometry and layout. Leave out administrative text."
    )
    return llm.call(llm.Extraction, prompt, max_tokens=32000)


def review(name: str, data: bytes, doc_ids: list[str] | None = None, progress=None) -> Review:
    def tick(frac: float, msg: str) -> None:
        if progress:
            progress(frac, msg)

    tick(0.05, "Extracting text")
    pages = drawings.extract(name, data)
    full_text = "\n".join(p.text for p in pages)
    live = llm.mode() == "live"
    error = ""
    if not full_text.strip():
        error = ("No text could be read from this file. Scanned pages need Tesseract OCR installed or a Claude API key "
                 "(for Claude vision).")
    kind, title_block = "other", ""
    statements: list[llm.ExtractedStatement] = []
    if live:
        tick(0.15, "Identifying technical statements")
        try:
            ex = _extract_live(name, pages)
            kind, title_block, statements = ex.document_kind, ex.title_block, ex.statements
        except llm.LLMUnavailable as exc:
            error, live = str(exc), False
    if not live:
        kind = "drawing" if DRAWING_HINT.search(full_text) or _is_image(name) else "report"
        statements = heuristic_statements(pages, drawing=kind == "drawing")

    rows: list[ReviewRow] = []
    missing: list[MissingRow] = []
    rejected: list[Rejection] = []
    with store.session() as conn:
        per_stmt_hits = []
        for i, s in enumerate(statements):
            per_stmt_hits.append(search.search(f"{s.topic} {s.statement}", 4, doc_ids, conn))
        batch_size = 8
        for start in range(0, len(statements), batch_size):
            tick(0.25 + 0.6 * start / max(len(statements), 1), f"Checking statements {start + 1}–{min(start + batch_size, len(statements))} of {len(statements)}")
            batch = list(range(start, min(start + batch_size, len(statements))))
            clause_list, seen = [], set()
            for i in batch:
                for h in per_stmt_hits[i]:
                    if h.clause.id not in seen:
                        seen.add(h.clause.id)
                        clause_list.append(h.clause)
            labels = {c.id: f"C{n}" for n, c in enumerate(clause_list, 1)}
            v = Verifier(clause_list, conn)
            findings: dict[int, llm.Finding] = {}
            if live and clause_list:
                stmts = "\n".join(
                    f'<statement id="{i + 1}" location="{statements[i].location}" candidate_clauses="{", ".join(labels[h.clause.id] for h in per_stmt_hits[i])}">{statements[i].statement}</statement>'
                    for i in batch)
                prompt = (f"<clauses>\n{llm.format_clauses(clause_list)}\n</clauses>\n\n<statements>\n{stmts}\n</statements>\n\n"
                          "For each statement, check it against the clauses. RAG: Green = complies with a clause; "
                          "Amber = partly complies, ambiguous, or needs clarification; Red = conflicts with a clause; "
                          "Not covered = no supplied clause addresses it. Quote the governing clause verbatim. "
                          "Write the comment as a reviewer would issue it to the contractor.")
                try:
                    out = llm.call(llm.ReviewBatch, prompt)
                    findings = {f.statement_id - 1: f for f in out.findings}
                except llm.LLMUnavailable as exc:
                    error, live = str(exc), False
            for i in batch:
                s = statements[i]
                f = findings.get(i)
                cands = [h.clause.citation for h in per_stmt_hits[i]]
                if f is None:
                    top = per_stmt_hits[i][0].clause if per_stmt_hits[i] else None
                    rows.append(ReviewRow(i + 1, s.location, s.statement, [top.citation] if top else [], "",
                                          "Not assessed (offline) — closest clause shown for manual check." if top else "No matching clause.",
                                          "Not assessed" if top else "Not covered", "", False, cands))
                    continue
                cits = []
                for ref in f.refs:
                    c = v.clause_for(ref)
                    if c is not None:
                        cits.append(c.citation)
                verified_quote = False
                if f.quote.strip() and f.refs:
                    verified_quote = any(v.quote(ref, f.quote) for ref in f.refs[:1])
                rag = f.rag
                comment = v.text(f.comment)
                if f.rag in ("Green", "Red") and not verified_quote:
                    rag = "Amber"
                    comment = (comment + " [Tool note: supporting quote could not be verified against the library — check manually.]").strip()
                rows.append(ReviewRow(i + 1, s.location, s.statement, cits, f.quote if verified_quote else "",
                                      v.text(f.finding), rag, comment, verified_quote, cands))
            rejected += v.result.rejected

        if kind == "drawing":
            tick(0.9, "Checking for notes the specifications require")
            missing, rej = _missing_notes(conn, full_text, statements, doc_ids, live)
            rejected += rej
        tick(1.0, "Done")
        rev = Review(name, not live, config.CLAUDE_MODEL if live else "offline-extractive", kind, title_block,
                     pages, rows, missing, rejected, error)
        store.log_query(conn, "review", name, {"rows": [r.__dict__ for r in rows], "missing": [m.__dict__ for m in missing],
                                                "title_block": title_block, "error": error},
                        sorted({c for r in rows for c in r.citations}), [r.detail for r in rejected], rev.model)
    return rev


def _is_image(name: str) -> bool:
    return name.lower().rsplit(".", 1)[-1] in ("png", "jpg", "jpeg", "tif", "tiff", "bmp")


def _missing_notes(conn, text: str, statements, doc_ids, live: bool) -> tuple[list[MissingRow], list[Rejection]]:
    queries = ["drawings shall clearly indicate main dimensions materials finishes",
               "construction drawings shall show", "drawings shall be noted colour coded"]
    queries += [s.topic for s in statements[:12]]
    seen, clauses = set(), []
    for q in queries:
        for h in search.search(q, 3, doc_ids, conn):
            if h.clause.id not in seen:
                seen.add(h.clause.id)
                clauses.append(h.clause)
    clauses = clauses[:20]
    if not live or not clauses:
        return [], []
    prompt = (f"<clauses>\n{llm.format_clauses(clauses)}\n</clauses>\n\n<drawing_text>\n{text[:60000]}\n</drawing_text>\n\n"
              "From the clauses, list the requirements that a drawing of this subject is expected to state in its notes "
              "or callouts (for example materials and grades, dimensions/thicknesses, capacities, finishes, standards, "
              "drawing information the specification requires). Only include requirements a supplied clause actually "
              "states and that are relevant to what this drawing shows. For each, say whether the drawing text states "
              "it (Present), does not (Missing) or is ambiguous (Unclear). Quote the clause verbatim.")
    try:
        out = llm.call(llm.MissingNotes, prompt)
    except llm.LLMUnavailable:
        return [], []
    v = Verifier(clauses, conn)
    rows = []
    for item in out.items:
        q = v.quote(item.ref, item.quote)
        if q is None:
            continue  # unverifiable requirement: drop rather than show
        rows.append(MissingRow(item.requirement, q.clause.citation, q.quote, item.status))
    return rows, v.result.rejected
