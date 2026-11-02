# Demo scenarios

Three canned scenarios, one per mode, with the answer key a reviewer would expect. All clause references are to
**SUB-03-034 Issue 5** unless stated, and were checked against the parsed library. Claude's wording will vary from run
to run; the positions, RAG ratings and clauses should match. Set the sidebar scope to
**275/400kV substation or HVDC converter station (EGL1)** before running.

---

## 1. Ask

**Question** (first example button on the Ask page):

> What capacity must a transformer oil containment bund be designed to hold, and how thick must reinforced concrete bund walls be?

**Expected answer: covered**

| Requirement | Clause |
|---|---|
| At least 115% of total oil content, or 125% of the largest item where a bund holds more than one oil-containing item | 12.9.1, p.29 |
| Also at least 100% of total oil content plus 150mm freeboard; voids in gravel ignored | 12.9.1, p.29 |
| Reinforced concrete bunds not less than 225mm thick, crack width controlled to 0.2mm | 12.9.1, p.29 |

You may also see: walls at least 300mm above finished level, inner face at least 1m clear of oil-containing parts,
penetrations not permitted (12.9.1), and the matching SUB-01-012 clause 10.4.4 on bunding outdoor transformers.

**Follow-up showing honesty about gaps.** Ask *"What is the minimum concrete cover to reinforcement for transformer
bund walls?"* The expected answer is **partly covered**. Clause 12.5 (p.20) says *"Exposure class and minimum cover to
reinforcement shall be appropriate for the site and ground specific conditions in accordance with the civil design."*
The library sets no figure, so the tool should say so and point to BS EN 1992-1-1 / BS 8500-1 as the likely governing
standards, without quoting values from them.

**Not-covered example.** Ask *"Is C40/50 concrete required for bund walls?"* "C40/50" appears nowhere in the library,
and the tool reports that. The library's minimum for bund walls is C32/40 (Table 2 in 12.5.3).

---

## 2. RFI

**RFI** (Load example RFI on the RFI page):

> RFI-EGL1-CIV-047 – Transformer bund, Torness 400kV compound. To suit the precast supplier's standard units we
> propose: (a) bund walls 200mm thick precast reinforced concrete; (b) bund volume of 110% of the transformer oil
> volume; (c) C28/35 concrete for the bund walls; and (d) a 100mm cable duct through the bund wall, sealed with a
> proprietary fire-rated sealant. Please confirm this is acceptable.

**Expected position: Non-compliant**

| Item | Finding | Clause |
|---|---|---|
| (a) 200mm walls | Below the 225mm minimum for reinforced concrete bunds. A precast/proprietary system needs prior acceptance by ED&S | 12.9.1 |
| (b) 110% | Below the 115% minimum (125% of the largest item for shared bunds); 100% + 150mm freeboard must also be met | 12.9.1 |
| (c) C28/35 | Below the C32/40 minimum strength class for bund walls, buried or exposed | 12.5 and Table 2 in 12.5.3 |
| (d) Duct through wall | "Penetrations for services are not permitted"; no duct or pipe shall pass through bund systems | 12.9.1; 12.9 |

The draft response should reject the proposal and cite each clause.

---

## 3. Document review

### 3a. Design statement: `EGL1-DEMO-CIV-DS-001_Design_Statement.docx`

| § | Statement | Expected RAG | Deciding clause |
|---|---|---|---|
| 2.1 | Bunds sized for 110% | **Red** (115% min) | 12.9.1 |
| 2.2 | 250mm RC walls, 0.2mm crack width | Green | 12.9.1 |
| 2.3 | Walls 300mm above finished level | Green | 12.9.1 |
| 2.4 | 100mm duct through bund wall | **Red** (penetrations not permitted) | 12.9.1; 12.9 |
| 2.5 | Water test until fall < 5mm in 24h | **Red** (< 3mm in 24h) | 12.9.3 |
| 3.1 | C28/35, CEM I for early strength | **Red** (C32/40 min; CEM I restricted, admixtures first) | 12.5.3 Table 2; 12.5 |
| 3.2 | 40mm cover, XC4/XD1 | Amber / Not covered (spec defers to the civil design) | 12.5 |
| 3.3 | 50mm C16/20 blinding | Green | 12.5.2; Table 2 |
| 4.1 | Bearing pressure 75 kN/m² | **Red** (100 kN/m² minimum) | 12.3 |
| 4.2 | Galvanising 70 microns | **Red** (85 microns minimum) | 12.15 |
| 4.3 | Base plates 25mm above foundations, non-shrink grout | Green | 12.16 |
| 5.1 | No flooding in 1 in 30 year event + 40% CC | Amber (1:25 met; 1:1000 "no standing water" check not addressed; CC allowance per agency) | 12.8.1 |
| 5.2 | 3.0mm 'W' pales, 100mm gaps | **Red** (85mm maximum clear space) | 12.11.2 |

### 3b. Drawing: `EGL1-DEMO-CIV-DRG-0101_Bund_GA.pdf` (vector) or `…_scan.png` (scanned)

The title block should read EGL1-DEMO-CIV-DRG-0101, Rev P02, For Acceptance.

| Note | Text | Expected RAG | Clause |
|---|---|---|---|
| 2 | C32/40, CEM II/B-V | Green | Table 2 (12.5.3); 12.5 |
| 3 | B500B, nominal cover 50mm | Amber / Not covered (cover is left to design) | 12.5 |
| 4 | Bund wall 200mm | **Red** (225mm min) | 12.9.1 |
| 5 | Capacity 115% | Green | 12.9.1 |
| 6 | Upstand 300mm | Green | 12.9.1 |
| 7 | Sump 900 × 900, 450mm downstand | Green | 12.9.1 |
| 8 | 300mm 14–20mm recycled angular stone | Green | 12.9.1 |
| 9 | Water tested on completion | Green | 12.9.1; 12.9.3 |

**Notes the specs require but the drawing omits:** 100% + 150mm freeboard; 0.2mm crack-width control; inner face at
least 1m clear of oil-containing parts; no service penetrations (12.9.1). Also expect the GA requirement to *"clearly
indicate the main dimensions, material and forms of construction"* (10.3).

The scanned PNG has no text layer. With Tesseract installed it is read by OCR; otherwise by Claude vision. Offline
with no OCR, the tool says it could not read the sheet.
