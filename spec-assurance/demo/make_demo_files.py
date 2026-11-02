"""Generate the demo contractor submissions in demo/inputs/.

All three are fictitious, marked DEMO, and deliberately contain known
compliant and non-compliant statements (see demo/SCENARIOS.md for the expected
findings and the clauses that decide them).

    python demo/make_demo_files.py
"""

from __future__ import annotations

from pathlib import Path

import pymupdf
from docx import Document
from docx.shared import Pt

OUT = Path(__file__).resolve().parent / "inputs"
DEMO = "DEMO – FICTITIOUS CONTRACTOR SUBMISSION – NOT AN SPT DOCUMENT"

STATEMENT_SECTIONS = [
    ("1 Introduction", [
        "This design statement covers the civil works for the transformer bunds and AIS equipment foundations at the "
        "Torness converter station AC substation compound (400kV), Eastern Green Link 1.",
    ]),
    ("2 Oil Containment", [
        "2.1 Transformer oil containment bunds are sized to contain 110% of the transformer oil volume.",
        "2.2 Bund walls are 250mm thick reinforced concrete designed to BS EN 1992-3, with crack width limited to 0.2mm.",
        "2.3 Bund walls stand 300mm above the adjacent finished compound level.",
        "2.4 A 100mm uPVC cable duct passes through the bund wall and will be sealed with a proprietary fire-rated sealant.",
        "2.5 On completion the bund will be water tested by filling to plinth level and monitoring until the fall in level is less than 5mm in 24 hours.",
    ]),
    ("3 Concrete and Reinforcement", [
        "3.1 Concrete to bund walls and transformer plinths shall be C28/35 using a CEM I mix to achieve early strength.",
        "3.2 Minimum nominal cover to reinforcement is 40mm for exposure class XC4/XD1.",
        "3.3 A 50mm C16/20 blinding layer is provided beneath all cast in situ foundations.",
    ]),
    ("4 Foundations and Steelwork", [
        "4.1 Foundations bear on undisturbed strata with an allowable bearing pressure of 75 kN/m².",
        "4.2 Equipment support structures are S355 steel, hot dip galvanised to BS EN ISO 1461 with a minimum coating thickness of 70 microns.",
        "4.3 Base plates are set 25mm above foundations and the void filled with non-shrink grout.",
    ]),
    ("5 Drainage and Fencing", [
        "5.1 The surface water system is designed for no flooding in the 1 in 30 year event including a 40% climate change allowance.",
        "5.2 Palisade fencing uses 3.0mm thick 'W' section pales with a maximum clear space of 100mm between pales.",
    ]),
]

DRAWING_NOTES = [
    "ALL DIMENSIONS ARE IN MILLIMETRES UNLESS NOTED OTHERWISE. DO NOT SCALE.",
    "CONCRETE TO BUND WALLS AND PLINTHS: C32/40 TO BS 8500-1, CEM II/B-V.",
    "REINFORCEMENT: B500B TO BS 4449. NOMINAL COVER 50mm.",
    "BUND WALL THICKNESS 200mm REINFORCED CONCRETE.",
    "BUND CAPACITY: 115% OF TRANSFORMER OIL VOLUME (68,000 LITRES).",
    "BUND WALL UPSTAND 300mm ABOVE FINISHED COMPOUND LEVEL.",
    "SUMP 900 x 900mm ON PLAN WITH 450mm DOWNSTAND.",
    "STONE INFILL: 300mm MINIMUM DEPTH OF RECYCLED 14-20mm ANGULAR STONE.",
    "BUND TO BE WATER TESTED ON COMPLETION.",
]


def make_statement() -> Path:
    d = Document()
    d.styles["Normal"].font.name = "Arial"
    d.styles["Normal"].font.size = Pt(10)
    d.add_paragraph(DEMO).runs[0].bold = True
    d.add_heading("Civil Design Statement – Transformer Bunds and AIS Foundations", level=1)
    d.add_paragraph("Document No. EGL1-DEMO-CIV-DS-001   Revision P01   Status: For Acceptance")
    d.add_paragraph("Prepared by: Demo Civils Ltd (fictitious)")
    for heading, paras in STATEMENT_SECTIONS:
        d.add_heading(heading, level=2)
        for p in paras:
            d.add_paragraph(p)
    path = OUT / "EGL1-DEMO-CIV-DS-001_Design_Statement.docx"
    d.save(path)
    return path


def make_drawing() -> Path:
    doc = pymupdf.open()
    page = doc.new_page(width=1191, height=842)  # A3 landscape, points
    navy = (0.12, 0.22, 0.39)
    page.draw_rect(pymupdf.Rect(20, 20, 1171, 822), color=(0, 0, 0), width=1.5)
    page.insert_text((40, 45), DEMO, fontsize=11, color=(0.75, 0, 0))

    # Plan: bund outline, plinth, sump (geometry is not assessed — context only)
    page.draw_rect(pymupdf.Rect(80, 120, 560, 520), color=navy, width=2)
    page.draw_rect(pymupdf.Rect(96, 136, 544, 504), color=navy, width=0.8)
    page.draw_rect(pymupdf.Rect(200, 220, 440, 420), color=(0.3, 0.3, 0.3), width=1, fill=(0.92, 0.92, 0.92))
    page.draw_rect(pymupdf.Rect(480, 440, 530, 490), color=(0.3, 0.3, 0.3), width=1)
    page.insert_text((250, 325), "TRANSFORMER PLINTH", fontsize=10)
    page.insert_text((470, 505), "SUMP", fontsize=8)
    page.insert_text((80, 545), "PLAN ON TRANSFORMER BUND  SCALE 1:100", fontsize=11, color=navy)
    page.insert_text((80, 110), "GRID A", fontsize=8)
    page.insert_text((540, 110), "GRID B", fontsize=8)

    # Notes
    x, y = 640, 120
    page.insert_text((x, y), "GENERAL NOTES", fontsize=12, color=navy)
    y += 22
    for i, note in enumerate(DRAWING_NOTES, 1):
        words, line = note.split(), ""
        first = True
        for w in words:
            if len(line) + len(w) > 62:
                page.insert_text((x, y), (f"{i}. " if first else "    ") + line, fontsize=9)
                y, line, first = y + 13, "", False
            line = (line + " " + w).strip()
        page.insert_text((x, y), (f"{i}. " if first else "    ") + line, fontsize=9)
        y += 18

    # Title block
    tb = pymupdf.Rect(640, 640, 1160, 810)
    page.draw_rect(tb, color=(0, 0, 0), width=1)
    rows = [
        ("CLIENT", "SP TRANSMISSION – EASTERN GREEN LINK 1 (DEMO)"),
        ("PROJECT", "TORNESS 400kV AC COMPOUND"),
        ("TITLE", "TRANSFORMER BUND – GENERAL ARRANGEMENT"),
        ("DRAWING No.", "EGL1-DEMO-CIV-DRG-0101"),
        ("REVISION", "P02"),
        ("STATUS", "FOR ACCEPTANCE"),
        ("SCALE", "1:100 @ A3"),
        ("DRAWN / CHECKED", "DEMO CIVILS LTD"),
    ]
    yy = tb.y0 + 16
    for k, v in rows:
        page.insert_text((tb.x0 + 8, yy), k, fontsize=8, color=(0.4, 0.4, 0.4))
        page.insert_text((tb.x0 + 120, yy), v, fontsize=9)
        page.draw_line((tb.x0, yy + 5), (tb.x1, yy + 5), color=(0.7, 0.7, 0.7), width=0.4)
        yy += 20
    path = OUT / "EGL1-DEMO-CIV-DRG-0101_Bund_GA.pdf"
    doc.save(path)

    # A raster copy, as if scanned: no text layer, forces OCR / Claude vision.
    png = OUT / "EGL1-DEMO-CIV-DRG-0101_Bund_GA_scan.png"
    page.get_pixmap(dpi=110).save(png)
    return path


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    print(make_statement())
    print(make_drawing())
