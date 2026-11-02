"""Check every citation and quote in a model answer against the database.

Nothing reaches the screen or an export unless it passes here:
* a [Cn] label must be one of the clauses actually supplied to the model;
* a quote must appear verbatim (modulo whitespace/typography) in that clause;
* any clause written out in prose ("SUB-03-034 clause 12.9.1") must exist.
Failures are removed from the answer and listed as rejected, so the reviewer
can see the tool caught them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import store
from .store import ClauseRow

LABEL = re.compile(r"\[?\b(C\d{1,2})\b\]?")
LABEL_BRACKETED = re.compile(r"\[((?:C\d{1,2})(?:\s*[,;/&]\s*C\d{1,2})*)\]")
PROSE_REF = re.compile(
    r"\b([A-Z]{2,6}-\d{2}-\d{3})\b[^.\n\[\]]{0,40}?\b(?:[Cc]lause|[Ss]ection|cl\.)\s*(\d{1,2}(?:\.\d{1,2}){0,5})"
)

_TYPO = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-", " ": " ", "•": " "})


def normalise(text: str) -> str:
    t = text.translate(_TYPO).replace("[Table]", " ").replace("|", " ")
    t = re.sub(r"(\w)-\s+(\w)", r"\1-\2", t)  # hyphen split across lines
    return re.sub(r"\s+", " ", t).strip().lower()


def quote_in_clause(quote: str, clause: ClauseRow) -> bool:
    hay = normalise(clause.text + " " + clause.heading)
    parts = [p for p in re.split(r"\s*(?:\.\.\.|…|\[\.\.\.\])\s*", quote) if p.strip()]
    if not parts:
        return False
    return all(normalise(p).strip(" .;,") in hay for p in parts)


@dataclass
class Verified:
    clause: ClauseRow
    quote: str


@dataclass
class Rejection:
    kind: str  # unknown_label | not_verbatim | unknown_clause
    detail: str


@dataclass
class Verification:
    quotes: list[Verified] = field(default_factory=list)
    rejected: list[Rejection] = field(default_factory=list)
    cited: dict[int, ClauseRow] = field(default_factory=dict)  # clause id → row

    @property
    def cited_list(self) -> list[str]:
        return [c.citation for c in self.cited.values()]


class Verifier:
    def __init__(self, supplied: list[ClauseRow], conn=None):
        self.supplied = supplied
        self.labels = {f"C{i}": c for i, c in enumerate(supplied, 1)}
        self.conn = conn
        self.result = Verification()

    def clause_for(self, ref: str) -> ClauseRow | None:
        c = self.labels.get(ref.strip().strip("[]").upper())
        if c is None:
            self.result.rejected.append(Rejection("unknown_label", f"{ref} was not one of the supplied clauses"))
        return c

    def quote(self, ref: str, quote: str) -> Verified | None:
        c = self.clause_for(ref)
        if c is None or not quote.strip():
            return None
        if not quote_in_clause(quote, c):
            self.result.rejected.append(Rejection("not_verbatim", f"Quote attributed to {c.citation} not found verbatim: “{quote[:160]}”"))
            return None
        v = Verified(c, quote.strip())
        self.result.quotes.append(v)
        self.result.cited[c.id] = c
        return v

    def text(self, text: str) -> str:
        """Replace [Cn] labels with full citations; strip invalid labels; check prose references."""
        if not text:
            return text

        def sub(m: re.Match) -> str:
            out = []
            for ref in re.split(r"\s*[,;/&]\s*", m.group(1)):
                c = self.clause_for(ref)
                if c is not None:
                    self.result.cited[c.id] = c
                    out.append(c.citation)
            return " ".join(out) if out else "[unverified reference removed]"

        text = LABEL_BRACKETED.sub(sub, text)
        for m in PROSE_REF.finditer(text):
            doc_id, clause_no = m.group(1), m.group(2)
            if self.conn is not None and store.find_clause(self.conn, doc_id, clause_no) is None:
                self.result.rejected.append(Rejection("unknown_clause", f"{doc_id} clause {clause_no} does not exist in the library"))
                text = text.replace(m.group(0), m.group(0) + " [not found in library]")
        return text


CITATION = re.compile(r"\[([A-Z]{2,6}-\d{2}-\d{3}), ([^,\]]+), Clause (\d{1,2}(?:\.\d{1,2}){0,5}), (p\.–|p\.(\d+)|pp\.(\d+)–(\d+))\]")


def check_citation(conn, citation: str) -> bool:
    """True if a rendered citation names a real clause, revision and page range."""
    m = CITATION.fullmatch(citation.strip())
    if not m:
        return False
    doc_id, revision, clause_no = m.group(1), m.group(2), m.group(3)
    row = store.find_clause(conn, doc_id, clause_no)
    if row is None or row.revision != revision:
        return False
    return row.citation == citation.strip()
