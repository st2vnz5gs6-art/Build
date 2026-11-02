"""Split a document's text stream into numbered clauses.

The parsers (PDF / DOCX) turn a document into an ordered list of `Block`s —
one per text line or table — with header/footer furniture already removed.
This module finds the clause headings in that stream (``10.4.6 Discharges to
Surface Water...``) and groups the text between them into `Clause`s.

A line is only accepted as a heading when its number is a plausible next
number after the previous heading (so ``3.`` inside a numbered list in clause
10.4 is not mistaken for clause 3), and — where the document has a contents
page — when it agrees with the contents for the levels the contents lists.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

NUM = r"\d{1,2}(?:\.\d{1,2}){0,5}"
HEADING_SAME_LINE = re.compile(rf"^({NUM})\.?\s+(\S.*?)\s*$")
NUMBER_ONLY = re.compile(rf"^({NUM})\.?\s*$")
# Layout quirk: the number lands after the heading text ("SPECIFIC GUIDANCE ... 12.").
HEADING_NUMBER_LAST = re.compile(rf"^(\D.*?)\s+({NUM})\.?\s*$")
DOT_LEADER = re.compile(r"\.{5,}|…{3,}")
TOC_ENTRY = re.compile(rf"^({NUM})\.?\s+(.+?)\s*(?:\.{{3,}}|…+)\s*\.?\s*(\d+)\s*$")
TOC_TITLE_ONLY = re.compile(r"^(.+?)\s*(?:\.{3,}|…+)\s*\.?\s*(\d+)\s*$")

# Words that start body text, never a heading, even after a number ("2 No. ducts").
NOT_HEADING_START = re.compile(r"^(No\.?|nr\.?|mm\b|m\b|kV\b|kN\b|x\b|%|and\b|or\b|of\b|to\b)", re.I)


@dataclass
class Block:
    page: int | None
    text: str
    kind: str = "line"  # line | table
    bold: bool = False
    new_para: bool = False  # vertical gap before this line → paragraph break


@dataclass
class Clause:
    clause_no: str
    heading: str
    page_start: int | None
    page_end: int | None
    parts: list[str] = field(default_factory=list)
    order: int = 0

    @property
    def parent_no(self) -> str | None:
        return self.clause_no.rsplit(".", 1)[0] if "." in self.clause_no else None

    @property
    def depth(self) -> int:
        return self.clause_no.count(".") + 1

    @property
    def text(self) -> str:
        return "\n".join(p for p in self.parts if p.strip()).strip()


def _nums(clause_no: str) -> list[int]:
    return [int(x) for x in clause_no.split(".")]


def plausible_next(prev: list[int] | None, cand: list[int]) -> bool:
    """Is `cand` a believable heading number straight after `prev`?"""
    if prev is None:
        return cand in ([1], [0]) or (len(cand) == 1 and cand[0] <= 2)
    # A child: 10.4 → 10.4.1 (or 10.4.1.1 where the intermediate has no heading).
    if cand[: len(prev)] == prev and all(x == 1 for x in cand[len(prev):]) and len(cand) - len(prev) <= 2:
        return True
    # A sibling or an ancestor's sibling: 10.4.6 → 10.4.7, 10.5, 11 — tolerate one skipped number.
    for k in range(len(prev)):
        if len(cand) == k + 1 and cand[:k] == prev[:k] and 1 <= cand[k] - prev[k] <= 2:
            return True
        # ...or that new section's first child: 10.4.6 → 11.1
        if len(cand) == k + 2 and cand[:k] == prev[:k] and 1 <= cand[k] - prev[k] <= 2 and cand[k + 1] == 1:
            return True
    return False


def looks_like_heading_text(text: str) -> bool:
    t = text.strip()
    if not t or len(t) > 120 or len(t.split()) > 16:
        return False
    if not (t[0].isupper() or t[0] in "‘'\"(“"):
        return False
    if NOT_HEADING_START.match(t):
        return False
    if t.endswith((".", ";", ",")) and not t.endswith(("etc.", "e.g.")):
        return False
    if re.search(r"\b(shall|must|should|will be|is to|are to)\b", t, re.I):
        return False
    return True


# --------------------------------------------------------------------------- contents page

def parse_toc(lines: list[str]) -> dict[str, str]:
    """Clause number → heading, from the contents page lines (dot leaders)."""
    toc: dict[str, str] = {}
    pending_no: str | None = None
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        m = NUMBER_ONLY.match(line)
        if m:
            pending_no = m.group(1)
            continue
        m = TOC_ENTRY.match(line)
        if m:
            toc[m.group(1)] = _clean_heading(m.group(2))
            pending_no = None
            continue
        m = TOC_TITLE_ONLY.match(line)
        if m and pending_no:
            toc[pending_no] = _clean_heading(m.group(1))
        pending_no = None
    return toc


def _clean_heading(h: str) -> str:
    return re.sub(r"\s+", " ", h).strip(" .:")


def _norm(h: str) -> str:
    return re.sub(r"[^a-z0-9]", "", h.lower())


# --------------------------------------------------------------------------- segmentation

def segment(blocks: list[Block], toc: dict[str, str] | None = None) -> list[Clause]:
    toc = toc or {}
    toc_depth = max((k.count(".") + 1 for k in toc), default=0)
    clauses: list[Clause] = []
    current: Clause | None = None
    prev_num: list[int] | None = None
    buf: list[str] = []  # current paragraph's lines

    def flush_para() -> None:
        if buf and current is not None:
            current.parts.append(" ".join(s.strip() for s in buf if s.strip()))
        buf.clear()

    def accept(no: str, heading: str) -> bool:
        cand = _nums(no)
        if not plausible_next(prev_num, cand):
            return False
        depth = len(cand)
        if toc and depth <= toc_depth:
            if no not in toc:
                return False
            # Heading must start like the contents entry (contents can abbreviate).
            a, b = _norm(heading), _norm(toc[no])
            if a and b and not (a.startswith(b[:12]) or b.startswith(a[:12])):
                return False
        return looks_like_heading_text(heading)

    i = 0
    while i < len(blocks):
        blk = blocks[i]
        if blk.kind == "table":
            flush_para()
            if current is not None:
                current.parts.append(blk.text)
                current.page_end = blk.page
            i += 1
            continue

        line = blk.text.strip()
        heading_found: tuple[str, str, int] | None = None  # (no, heading, lines consumed)
        m = NUMBER_ONLY.match(line)
        if m and i + 1 < len(blocks) and blocks[i + 1].kind == "line":
            nxt = blocks[i + 1].text.strip()
            if accept(m.group(1), nxt):
                heading_found = (m.group(1), nxt, 2)
        if heading_found is None:
            m = HEADING_SAME_LINE.match(line)
            if m and accept(m.group(1), m.group(2)):
                heading_found = (m.group(1), m.group(2), 1)
        if heading_found is None and toc:
            m = HEADING_NUMBER_LAST.match(line)
            if m and m.group(2) in toc and accept(m.group(2), m.group(1)):
                heading_found = (m.group(2), m.group(1), 1)

        if heading_found:
            flush_para()
            no, heading, used = heading_found
            heading = _clean_heading(heading)
            if toc.get(no) and len(toc[no]) > len(heading):
                heading = toc[no]  # contents page carries the full wrapped heading
            current = Clause(no, heading, blk.page, blk.page, order=len(clauses))
            clauses.append(current)
            prev_num = _nums(no)
            i += used
            continue

        if current is not None and line:
            if blk.new_para:
                flush_para()
            buf.append(line)
            current.page_end = blk.page
        i += 1
    flush_para()
    return clauses


def hierarchy_path(clauses: list[Clause]) -> dict[str, str]:
    """clause_no → 'Section heading › Sub heading' breadcrumb."""
    by_no = {c.clause_no: c.heading for c in clauses}
    out = {}
    for c in clauses:
        nums = c.clause_no.split(".")
        crumbs = []
        for k in range(1, len(nums)):
            key = ".".join(nums[:k])
            if key in by_no:
                crumbs.append(f"{key} {by_no[key]}")
        out[c.clause_no] = " › ".join(crumbs)
    return out
