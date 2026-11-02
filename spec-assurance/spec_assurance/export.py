"""Exports: Excel compliance table, Word assurance comment sheet, PDF (rendered by PyMuPDF)."""

from __future__ import annotations

import html
import io
from datetime import date

import pymupdf
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from .modes import Answer, Review

RAG_FILL = {"Green": "C6EFCE", "Amber": "FFEB9C", "Red": "FFC7CE", "Not covered": "D9D9D9", "Not assessed": "EDEDED",
            "Missing": "FFC7CE", "Present": "C6EFCE", "Unclear": "FFEB9C"}
NAVY = "1F3864"
DISCLAIMER = ("Prepared with the SPT Spec Assurance prototype. Clause references and quotes have been checked "
              "automatically against the library; engineering judgement remains with the reviewer.")


def _meta_lines(reviewer: str, project: str) -> list[tuple[str, str]]:
    return [("Project", project or "Eastern Green Link 1 (EGL1)"), ("Reviewer", reviewer or ""),
            ("Date", date.today().strftime("%d %B %Y"))]


# --------------------------------------------------------------------------- Excel

def review_to_excel(rev: Review, reviewer: str = "", project: str = "") -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Compliance table"
    thin = Side(style="thin", color="BFBFBF")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    ws["A1"] = "Design assurance compliance table"
    ws["A1"].font = Font(size=14, bold=True, color=NAVY)
    meta = [("Document reviewed", rev.filename), ("Title block", rev.title_block or "—")] + _meta_lines(reviewer, project)
    meta.append(("Assessment", "Offline (search only)" if rev.offline else f"Claude ({rev.model})"))
    for i, (k, v) in enumerate(meta, start=2):
        ws.cell(i, 1, k).font = Font(bold=True)
        ws.cell(i, 2, v)
    start = len(meta) + 3
    headers = ["No.", "Location", "Statement", "Relevant clause", "Verified quote", "Finding", "RAG", "Comment"]
    widths = [6, 16, 50, 34, 50, 45, 12, 50]
    for col, (h, w) in enumerate(zip(headers, widths), 1):
        c = ws.cell(start, col, h)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=NAVY)
        c.alignment = Alignment(vertical="center", wrap_text=True)
        c.border = border
        ws.column_dimensions[get_column_letter(col)].width = w
    for r, row in enumerate(rev.rows, start + 1):
        vals = [row.no, row.location, row.statement, "\n".join(row.citations), row.quote, row.finding, row.rag, row.comment]
        for col, v in enumerate(vals, 1):
            c = ws.cell(r, col, v)
            c.alignment = Alignment(vertical="top", wrap_text=True)
            c.border = border
        ws.cell(r, 7).fill = PatternFill("solid", fgColor=RAG_FILL.get(row.rag, "FFFFFF"))
    ws.freeze_panes = ws.cell(start + 1, 1)
    ws.auto_filter.ref = f"A{start}:H{start + len(rev.rows)}"

    if rev.missing:
        ws2 = wb.create_sheet("Required notes")
        for col, (h, w) in enumerate(zip(["Requirement", "Clause", "Quote", "Status"], [50, 34, 60, 12]), 1):
            c = ws2.cell(1, col, h)
            c.font = Font(bold=True, color="FFFFFF")
            c.fill = PatternFill("solid", fgColor=NAVY)
            ws2.column_dimensions[get_column_letter(col)].width = w
        for r, m in enumerate(rev.missing, 2):
            for col, v in enumerate([m.requirement, m.citation, m.quote, m.status], 1):
                ws2.cell(r, col, v).alignment = Alignment(vertical="top", wrap_text=True)
            ws2.cell(r, 4).fill = PatternFill("solid", fgColor=RAG_FILL.get(m.status, "FFFFFF"))

    if rev.rejected:
        ws3 = wb.create_sheet("Rejected citations")
        ws3.append(["Type", "Detail"])
        for rj in rev.rejected:
            ws3.append([rj.kind, rj.detail])
        ws3.column_dimensions["B"].width = 120

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# --------------------------------------------------------------------------- Word

def _shade(cell, hex_fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    tc_pr.append(shd)


def _doc(title: str, landscape: bool) -> Document:
    d = Document()
    sec = d.sections[0]
    if landscape:
        sec.orientation = WD_ORIENT.LANDSCAPE
        sec.page_width, sec.page_height = sec.page_height, sec.page_width
    for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(sec, side, Cm(1.8))
    style = d.styles["Normal"]
    style.font.name = "Arial"
    style.font.size = Pt(9.5)
    h = d.add_heading(title, level=1)
    for r in h.runs:
        r.font.color.rgb = RGBColor.from_string(NAVY)
    sec.footer.paragraphs[0].text = DISCLAIMER
    sec.footer.paragraphs[0].runs[0].font.size = Pt(7.5)
    return d


def _meta_table(d: Document, rows: list[tuple[str, str]]) -> None:
    t = d.add_table(rows=0, cols=2)
    t.style = "Table Grid"
    for k, v in rows:
        cells = t.add_row().cells
        cells[0].text, cells[1].text = k, v
        cells[0].paragraphs[0].runs[0].bold = True
        _shade(cells[0], "E7ECF5")
        cells[0].width, cells[1].width = Cm(4.5), Cm(20)
    d.add_paragraph()


def review_to_docx(rev: Review, reviewer: str = "", project: str = "") -> bytes:
    d = _doc("Design Assurance Comment Sheet", landscape=True)
    counts = ", ".join(f"{k}: {v}" for k, v in rev.rag_counts.items()) or "—"
    _meta_table(d, [("Document reviewed", rev.filename), ("Title block", rev.title_block or "—")]
                + _meta_lines(reviewer, project) + [("Summary", counts)])
    headers = ["No.", "Location", "Statement", "Clause", "Finding", "RAG", "Comment"]
    widths = [1.0, 2.4, 6.0, 3.6, 5.2, 1.8, 5.6]
    t = d.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = h
        c.paragraphs[0].runs[0].bold = True
        c.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        _shade(c, NAVY)
    for row in rev.rows:
        cells = t.add_row().cells
        finding = row.finding + (f"\n\n“{row.quote}”" if row.quote else "")
        vals = [str(row.no), row.location, row.statement, "\n".join(row.citations), finding, row.rag, row.comment]
        for i, v in enumerate(vals):
            cells[i].text = v
        _shade(cells[5], RAG_FILL.get(row.rag, "FFFFFF"))
    for row in t.rows:
        for i, w in enumerate(widths):
            row.cells[i].width = Cm(w)
    if rev.missing:
        d.add_heading("Notes required by the specifications", level=2)
        t2 = d.add_table(rows=1, cols=4)
        t2.style = "Table Grid"
        for i, h in enumerate(["Requirement", "Clause", "Quote", "Status"]):
            t2.rows[0].cells[i].text = h
            t2.rows[0].cells[i].paragraphs[0].runs[0].bold = True
        for m in rev.missing:
            cells = t2.add_row().cells
            for i, v in enumerate([m.requirement, m.citation, m.quote, m.status]):
                cells[i].text = v
            _shade(cells[3], RAG_FILL.get(m.status, "FFFFFF"))
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


def answer_to_docx(ans: Answer, reviewer: str = "", project: str = "") -> bytes:
    d = _doc("RFI Response – Design Assurance" if ans.mode == "rfi" else "Specification Query – Design Assurance", landscape=False)
    meta = _meta_lines(reviewer, project) + [("Coverage", ans.coverage.replace("_", " ").title())]
    if ans.mode == "rfi":
        meta.append(("Compliance position", ans.position))
    _meta_table(d, meta)
    d.add_heading("RFI" if ans.mode == "rfi" else "Question", level=2)
    d.add_paragraph(ans.query)
    if ans.mode == "rfi":
        d.add_heading("Position", level=2)
        d.add_paragraph(f"{ans.position}. {ans.position_basis}")
        d.add_heading("Draft response", level=2)
        d.add_paragraph(ans.draft_response)
    else:
        d.add_heading("Answer", level=2)
        d.add_paragraph(ans.answer)
    d.add_heading("What the specification says", level=2)
    for q in ans.quotes:
        p = d.add_paragraph(style="List Bullet")
        p.add_run(q.clause.citation + " ").bold = True
        p.add_run(f"“{q.quote}”").italic = True
    if not ans.quotes:
        d.add_paragraph("No supporting clause found in the library.")
    if ans.interpretation:
        d.add_heading("Interpretation", level=2)
        d.add_paragraph(ans.interpretation)
    if ans.gaps_conflicts or ans.likely_standard:
        d.add_heading("Gaps and conflicts", level=2)
        for g in ans.gaps_conflicts:
            d.add_paragraph(g, style="List Bullet")
        if ans.likely_standard:
            d.add_paragraph(f"Likely governing standard: {ans.likely_standard}", style="List Bullet")
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


# --------------------------------------------------------------------------- PDF

_CSS = """
body { font-family: sans-serif; font-size: 8.5pt; color: #222; }
h1 { font-size: 15pt; color: #1F3864; margin: 0 0 6pt 0; }
h2 { font-size: 11pt; color: #1F3864; margin: 10pt 0 4pt 0; }
table { border-collapse: collapse; width: 100%; }
td, th { border: 0.5pt solid #999; padding: 3pt; vertical-align: top; }
th { background-color: #1F3864; color: #fff; text-align: left; }
.q { font-style: italic; color: #444; }
.foot { font-size: 7pt; color: #666; margin-top: 10pt; }
"""


def _e(s: str) -> str:
    return html.escape(s or "").replace("\n", "<br/>")


def _meta_html(rows: list[tuple[str, str]]) -> str:
    return "".join(f'<p style="margin:1pt 0"><b>{_e(k)}:</b> {_e(v)}</p>' for k, v in rows)


def review_html(rev: Review, reviewer: str = "", project: str = "") -> str:
    counts = ", ".join(f"{k}: {v}" for k, v in rev.rag_counts.items()) or "—"
    rows = "".join(
        f"<tr><td>{r.no}</td><td>{_e(r.location)}</td><td>{_e(r.statement)}</td><td>{_e(chr(10).join(r.citations))}</td>"
        f"<td>{_e(r.finding)}{'<br/><span class=q>“' + _e(r.quote) + '”</span>' if r.quote else ''}</td>"
        f'<td style="background-color:#{RAG_FILL.get(r.rag, "FFFFFF")}">{_e(r.rag)}</td><td>{_e(r.comment)}</td></tr>'
        for r in rev.rows)
    missing = ""
    if rev.missing:
        missing = "<h2>Notes required by the specifications</h2><table><tr><th>Requirement</th><th>Clause</th><th>Quote</th><th>Status</th></tr>" + "".join(
            f'<tr><td>{_e(m.requirement)}</td><td>{_e(m.citation)}</td><td class="q">“{_e(m.quote)}”</td>'
            f'<td style="background-color:#{RAG_FILL.get(m.status, "FFFFFF")}">{_e(m.status)}</td></tr>' for m in rev.missing) + "</table>"
    return (f"<h1>Design Assurance Comment Sheet</h1>"
            + _meta_html([("Document reviewed", rev.filename), ("Title block", rev.title_block or "—")]
                         + _meta_lines(reviewer, project) + [("Summary", counts)])
            + "<h2>Compliance table</h2><table><tr><th>No.</th><th>Location</th><th>Statement</th><th>Clause</th>"
              "<th>Finding</th><th>RAG</th><th>Comment</th></tr>" + rows + "</table>" + missing
            + f'<p class="foot">{_e(DISCLAIMER)}</p>')


def answer_html(ans: Answer, reviewer: str = "", project: str = "") -> str:
    meta = _meta_lines(reviewer, project) + [("Coverage", ans.coverage.replace("_", " ").title())]
    if ans.mode == "rfi":
        meta.append(("Compliance position", ans.position))
    body = [f"<h1>{'RFI Response' if ans.mode == 'rfi' else 'Specification Query'} – Design Assurance</h1>", _meta_html(meta),
            f"<h2>{'RFI' if ans.mode == 'rfi' else 'Question'}</h2><p>{_e(ans.query)}</p>"]
    if ans.mode == "rfi":
        body += [f"<h2>Position</h2><p>{_e(ans.position)}. {_e(ans.position_basis)}</p>",
                 f"<h2>Draft response</h2><p>{_e(ans.draft_response)}</p>"]
    else:
        body.append(f"<h2>Answer</h2><p>{_e(ans.answer)}</p>")
    body.append("<h2>What the specification says</h2><ul>" + "".join(
        f'<li><b>{_e(q.clause.citation)}</b> <span class="q">“{_e(q.quote)}”</span></li>' for q in ans.quotes) + "</ul>")
    if ans.interpretation:
        body.append(f"<h2>Interpretation</h2><p>{_e(ans.interpretation)}</p>")
    gaps = list(ans.gaps_conflicts) + ([f"Likely governing standard: {ans.likely_standard}"] if ans.likely_standard else [])
    if gaps:
        body.append("<h2>Gaps and conflicts</h2><ul>" + "".join(f"<li>{_e(g)}</li>" for g in gaps) + "</ul>")
    body.append(f'<p class="foot">{_e(DISCLAIMER)}</p>')
    return "".join(body)


def html_to_pdf(body_html: str, landscape: bool = False) -> bytes:
    rect = pymupdf.paper_rect("a4-l" if landscape else "a4")
    where = rect + (36, 36, -36, -36)
    story = pymupdf.Story(html=body_html, user_css=_CSS)
    buf = io.BytesIO()
    writer = pymupdf.DocumentWriter(buf)
    more = True
    while more:
        dev = writer.begin_page(rect)
        more, _ = story.place(where)
        story.draw(dev)
        writer.end_page()
    writer.close()
    return buf.getvalue()
