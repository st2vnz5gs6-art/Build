"""PDF → ordered Blocks (lines and tables) + document metadata, via PyMuPDF."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import pymupdf

from .clauses import DOT_LEADER, Block

PAGE_X_OF_Y = re.compile(r"^\s*Page\s+\d+\s+of\s+\d+\s*$", re.I)
DOC_ID = re.compile(r"\b([A-Z]{2,6}-\d{2}-\d{3})\b")
ISSUE = re.compile(r"\b(?:Issue|Revision|Rev)\.?\s*(?:No\.?)?\s*(\d+[A-Z]?)\b", re.I)


@dataclass
class ParsedDoc:
    doc_id: str
    title: str
    revision: str
    pages: int
    blocks: list[Block]
    toc_lines: list[str]
    page_texts: list[str]  # raw text per page, for drawing/notes checks


def _norm_furniture(text: str) -> str:
    return re.sub(r"\d+", "#", text.strip().lower())


def _line_text(line: dict) -> str:
    return "".join(s["text"] for s in line["spans"]).replace(" ", " ")


def _line_bold(line: dict) -> bool:
    spans = [s for s in line["spans"] if s["text"].strip()]
    return bool(spans) and all(s["flags"] & 16 or "bold" in s["font"].lower() for s in spans)


def _is_contents_page(text: str) -> bool:
    return len(DOT_LEADER.findall(text)) >= 5


def _render_table(page: pymupdf.Page, table) -> str:
    grid: list[list[str | None]] = []
    for row in table.rows:
        cells = []
        for c in row.cells:
            if c is None:
                cells.append(None)
                continue
            t = re.sub(r"\s*\n\s*", " ", page.get_text("text", clip=c)).strip()
            cells.append(t)
        grid.append(cells)
    if not grid:
        return ""
    ncols = max(len(r) for r in grid)
    filled = [sum(1 for t in r if t) for r in grid]
    # Multi-row headers come out as several sparse rows: fold them column-wise into one.
    first_data = next((i for i in range(1, len(grid)) if filled[i] >= max(2, 0.6 * ncols)), 1)
    header_rows = grid[:first_data] if first_data > 1 else []
    rows_out = []
    if header_rows:
        header = []
        for col in range(ncols):
            parts = [r[col] for r in header_rows if col < len(r) and r[col]]
            if parts:
                header.append(re.sub(r"\s+", " ", " ".join(parts)).replace("- ", "-"))
        rows_out.append(" | ".join(header))
    for r in grid[len(header_rows):]:
        cells = [t for t in r if t]
        if cells:
            rows_out.append(" | ".join(cells))
    return "[Table]\n" + "\n".join(rows_out) if rows_out else ""


def parse_pdf(path: str | Path) -> ParsedDoc:
    doc = pymupdf.open(str(path))
    n = doc.page_count
    raw_pages = [p.get_text("dict") for p in doc]
    page_texts = [p.get_text() for p in doc]

    # Header/footer furniture: text that repeats near the top/bottom of most pages.
    furniture_counts: Counter[str] = Counter()
    for pi, pd in enumerate(raw_pages):
        h = doc[pi].rect.height
        seen = set()
        for b in pd["blocks"]:
            for ln in b.get("lines", []):
                y0, y1 = ln["bbox"][1], ln["bbox"][3]
                if y1 < h * 0.13 or y0 > h * 0.9:
                    seen.add(_norm_furniture(_line_text(ln)))
        furniture_counts.update(seen)
    threshold = max(2, int(n * 0.5))
    furniture = {t for t, c in furniture_counts.items() if c >= threshold and t}

    # Metadata from page 1 (and the repeated header text).
    first = page_texts[0] if page_texts else ""
    header_text = "\n".join(
        _line_text(ln) for b in raw_pages[0]["blocks"] for ln in b.get("lines", [])
        if _norm_furniture(_line_text(ln)) in furniture
    ) if raw_pages else ""
    m = DOC_ID.search(header_text) or DOC_ID.search(first) or DOC_ID.search(Path(path).stem)
    doc_id = m.group(1) if m else Path(path).stem
    m = ISSUE.search(header_text) or ISSUE.search(first)
    revision = f"Issue {m.group(1)}" if m else "Unknown"
    title_lines = []
    for raw in header_text.splitlines():
        t = raw.strip()
        if not t or DOC_ID.search(t) or ISSUE.search(t) or PAGE_X_OF_Y.match(t) or "©" in t or t.lower() == "internal use":
            continue
        title_lines.append(t)
    title = " ".join(title_lines).strip() or (doc.metadata or {}).get("title") or doc_id
    title = re.sub(r"\s+", " ", title)

    blocks: list[Block] = []
    toc_lines: list[str] = []
    for pi, pd in enumerate(raw_pages):
        page = doc[pi]
        page_no = pi + 1
        contents_page = _is_contents_page(page_texts[pi])
        if contents_page:
            toc_lines.extend(page_texts[pi].splitlines())

        tables = []
        if not contents_page and page.get_drawings():
            for t in page.find_tables().tables:
                rendered = _render_table(page, t)
                if rendered and not DOT_LEADER.search(rendered):
                    tables.append((pymupdf.Rect(t.bbox), rendered))

        items: list[tuple[float, Block]] = []
        for rect, rendered in tables:
            items.append((rect.y0, Block(page_no, rendered, kind="table")))

        prev_bottom = None
        lines = [ln for b in pd["blocks"] for ln in b.get("lines", [])
                 if _line_text(ln).strip() and _norm_furniture(_line_text(ln)) not in furniture
                 and not PAGE_X_OF_Y.match(_line_text(ln))]
        lines.sort(key=lambda ln: (ln["bbox"][1], ln["bbox"][0]))
        # Merge fragments sitting on the same baseline ("10.1" + "Consents"), left to right.
        groups: list[list[dict]] = []
        for ln in lines:
            if groups and abs(groups[-1][0]["bbox"][1] - ln["bbox"][1]) < 2.5:
                groups[-1].append(ln)
            else:
                groups.append([ln])
        merged: list[dict] = []
        for g in groups:
            g.sort(key=lambda ln: ln["bbox"][0])
            spans = []
            for ln in g:
                if spans:
                    spans.append({"text": " ", "flags": ln["spans"][0]["flags"], "font": ln["spans"][0]["font"]})
                spans.extend(ln["spans"])
            bbox = (min(ln["bbox"][0] for ln in g), min(ln["bbox"][1] for ln in g),
                    max(ln["bbox"][2] for ln in g), max(ln["bbox"][3] for ln in g))
            merged.append({"spans": spans, "bbox": bbox})
        for ln in merged:
            text = re.sub(r"\s{2,}", " ", _line_text(ln)).strip()
            if not text:
                continue
            if _norm_furniture(text) in furniture or PAGE_X_OF_Y.match(text):
                continue
            if contents_page and DOT_LEADER.search(text):
                continue
            x0, y0, x1, y1 = ln["bbox"]
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            if any(r.contains(pymupdf.Point(cx, cy)) for r, _ in tables):
                continue
            height = max(y1 - y0, 1)
            new_para = prev_bottom is None or (y0 - prev_bottom) > height * 0.45
            prev_bottom = y1
            if contents_page:
                continue  # contents lines feed the TOC only
            items.append((y0, Block(page_no, text, bold=_line_bold(ln), new_para=new_para)))

        items.sort(key=lambda it: it[0])
        blocks.extend(b for _, b in items)

    return ParsedDoc(doc_id, title, revision, n, blocks, toc_lines, page_texts)
