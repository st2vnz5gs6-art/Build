# SPT Spec Assurance (prototype)

A local design assurance tool for civil and structural work on SP Transmission projects (EGL1). It holds a library
of SP Energy Networks specifications, parsed clause by clause, and answers questions, RFIs and document reviews.
Every requirement it states quotes its source clause verbatim, cited as `[Doc ID, Revision, Clause X.X, p.N]`.

## Setup on Windows

You need Python 3.12, 3.13 or 3.14 (64-bit) from the Company Portal or python.org. Put the specification PDFs in
`library\` first (see `SOURCES.md`).

**Offline install (no internet or PyPI needed).** Use this when pip is blocked. Download the
`spec-assurance-offline` branch ZIP, which includes a `wheelhouse\` folder of every Windows package for Python
3.12–3.14. Then double-click **`install.bat`** and, once it finishes, **`run.bat`**.

**Online install (5 commands).** From this folder, in a Command Prompt:

```bat
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
streamlit run app.py
```

Open `.env` in Notepad and add your `ANTHROPIC_API_KEY`. The browser opens at http://localhost:8501. On first run
the library is indexed automatically (about a minute for six specifications).

Without an API key the tool runs in **offline mode**: search, clause browsing and extractive evidence work, but
nothing is interpreted, and every screen says so.

**Corporate network notes**
* `pip` behind a proxy: `pip install --proxy http://proxy:port -r requirements.txt`. For the app itself, set
  `HTTPS_PROXY` in `.env`.
* TLS inspection: `truststore` makes Python use the Windows certificate store, so the Claude API works without
  certificate tweaks.
* The embedding model is bundled in `models/`, so nothing is downloaded at runtime. Streamlit usage statistics are
  switched off in `.streamlit/config.toml`.
* Scanned drawings: install Tesseract OCR (e.g. UB-Mannheim build) if allowed, and set `TESSERACT_CMD` in `.env`.
  Without it, scanned sheets are transcribed by Claude vision.

## What it does

| Mode | Input | Output |
|---|---|---|
| **Ask** | Free-text question | Answer, verbatim clause quotes, interpretation, gaps/conflicts, coverage (covered / partial / not covered) |
| **RFI** | Pasted RFI | Position (Compliant / Non-compliant / Clarification needed), basis, quotes, editable draft response |
| **Document review** | Report, calc, design statement, or drawing (PDF vector/scanned, PNG/JPG/TIF, DOCX) | Compliance table: statement, clause, finding, RAG, comment. For drawings, also the notes the specs require that are missing |

Every result shows the retrieved clauses. Every citation can be clicked: it opens the clause text and the actual PDF
page with the quote highlighted. Results export to Excel and to Word/PDF comment sheets. Everything is logged in
the **Audit log** (question, answer, clauses cited, citations rejected, time, model).

The **sidebar scope** limits searches to the specification for the asset type (e.g. 275/400kV → SUB-03-034 plus the
fire and flood policies), so answers do not mix in requirements from a 33kV specification.

## How the evidence chain works

```
library/*.pdf ─► parse (PyMuPDF): strip headers/footers, keep tables, read contents page
             ─► split into clauses: number, heading, text, pages, parent section
             ─► SQLite (clauses + FTS5 keyword index) + local vector index (model2vec)
query ──────► hybrid search: BM25 keyword + semantic ─► reciprocal-rank fusion ─► term-coverage re-rank
          ──► top clauses labelled [C1]..[Cn] ─► Claude (strict citation-only system prompt, JSON schema output)
          ──► citation verifier: label must be a supplied clause; quote must appear verbatim; prose clause
              references must exist ─► anything failing is removed and listed as "rejected"
          ──► UI / exports / audit log
```

The clause splitter only accepts a heading when its number plausibly follows the previous one (so a numbered list
inside clause 10.4 is never read as clause 3). For the top two levels it must also match the contents page. On the
six supplied specifications this gives 671 clauses with no missing contents-page entries.

Conflict handling: `hierarchy.json` sets the order of precedence (contract-specific requirements > SPEN specifications
and policies > British/European standards > industry guidance) and the per-asset document scopes. The model is told
to report conflicts and which governs; documents in the same tier are referred to SPEN ED&S.

## Folder structure

```
app.py                  Streamlit entry point (navigation)
views/                  Pages: home, ask, rfi, review, library, log
spec_assurance/
  ingest/pdf_parser.py  PDF → lines/tables, furniture removal, metadata
  ingest/docx_parser.py DOCX → paragraphs/tables
  ingest/clauses.py     clause segmentation, contents-page parsing
  ingest/drawings.py    review-document text: PDF text → Tesseract → Claude vision
  store.py              SQLite schema, FTS5, audit log
  embed.py              local embeddings and vector search
  search.py             hybrid retrieval and re-ranking
  llm.py                Claude client, system prompt, answer schemas
  citations.py          citation and quote verifier
  modes.py              Ask / RFI / Review pipelines, offline fallbacks
  export.py             Excel, Word, PDF
  hierarchy.py          precedence and scope presets (hierarchy.json)
library/                specification PDFs (local only, not in git)
models/potion-base-8M/  bundled embedding model (MIT)
demo/                   demo inputs, generator script, SCENARIOS.md with expected outputs
tests/                  parser and citation-integrity tests
```

## Tests

```bat
python -m pytest -q
```

The tests build a temporary index from SUB-03-034 and SUB-01-012. They check the clause parsing (numbering order,
known clauses and pages, tables, no page furniture). They also replace Claude with a fake that returns real **and
fabricated** citations, then check that every citation the tool displays, exports or logs exists in the database
with the right revision and page, and that invented quotes, labels and clause numbers are caught.

## Demo

`demo/SCENARIOS.md` has the three scenarios (question, RFI, contractor review) with the expected answers and clauses.
The demo inputs can be picked straight from the Document review page. Regenerate them with
`python demo\make_demo_files.py`.

## Limits of the prototype

* It assures against the library only. It is not a substitute for checking the governing British/European standards,
  which are copyright and not included.
* Drawing review reads text only: notes, title block and callouts. Geometry and layout are not assessed.
* Clause parsing is tuned to the SPEN specification layout. A new document format should be checked in the
  Library view (clause list and counts) after indexing.
* Claude's interpretation can be wrong even when its quotes are verified. The interpretation is labelled as such,
  and engineering judgement stays with the reviewer.
