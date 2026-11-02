"""DOCX → ordered Blocks + metadata, via python-docx.

Word files carry no fixed pagination, so clauses from a DOCX have no page
number; citations show "p.–" for them.
"""

from __future__ import annotations

import re
from pathlib import Path

import docx
from docx.table import Table
from docx.text.paragraph import Paragraph

from .clauses import Block
from .pdf_parser import DOC_ID, ISSUE, ParsedDoc


def _iter_body(document):
    for child in document.element.body.iterchildren():
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            yield Paragraph(child, document)
        elif tag == "tbl":
            yield Table(child, document)


def _table_text(table: Table) -> str:
    rows = []
    for row in table.rows:
        cells, last = [], None
        for cell in row.cells:
            t = re.sub(r"\s+", " ", cell.text).strip()
            if t and t != last:  # merged cells repeat their text
                cells.append(t)
            last = t
        if cells:
            rows.append(" | ".join(cells))
    return "[Table]\n" + "\n".join(rows) if rows else ""


def parse_docx(path: str | Path) -> ParsedDoc:
    document = docx.Document(str(path))
    blocks: list[Block] = []
    plain: list[str] = []
    for item in _iter_body(document):
        if isinstance(item, Paragraph):
            text = item.text.strip()
            if not text:
                continue
            style = (item.style.name or "").lower() if item.style is not None else ""
            bold = style.startswith("heading") or all(r.bold for r in item.runs if r.text.strip())
            blocks.append(Block(None, text, bold=bold, new_para=True))
            plain.append(text)
        else:
            t = _table_text(item)
            if t:
                blocks.append(Block(None, t, kind="table"))
                plain.append(t)

    head = "\n".join(plain[:40])
    props = document.core_properties
    header_text = " ".join(p.text for s in document.sections for p in s.header.paragraphs)
    m = DOC_ID.search(header_text) or DOC_ID.search(head) or DOC_ID.search(Path(path).stem)
    doc_id = m.group(1) if m else Path(path).stem
    m = ISSUE.search(header_text) or ISSUE.search(head)
    revision = f"Issue {m.group(1)}" if m else (props.revision and f"Rev {props.revision}") or "Unknown"
    title = props.title or next((b.text for b in blocks if b.kind == "line" and not DOC_ID.search(b.text)), doc_id)
    return ParsedDoc(doc_id, title.strip(), revision, 0, blocks, [], ["\n".join(plain)])
