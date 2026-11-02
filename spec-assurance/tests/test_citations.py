"""No hallucinated clauses: every citation the tool returns must exist in the database.

The Claude call is replaced by a fake that returns a realistic mix of genuine
and fabricated citations, so the verifier is exercised without an API key.
"""

import re

import pytest

from spec_assurance import citations, llm, modes, search, store
from spec_assurance.citations import Verifier, check_citation, quote_in_clause

SCOPE = ["SUB-03-034", "SUB-01-012"]
LABELS = re.compile(r'label="(C\d+)"')


def _first_sentence(prompt: str, label: str) -> str:
    block = prompt.split(f'label="{label}"', 1)[1].split("</clause>", 1)[0]
    body = block.split("\n", 2)[2]  # skip attribute line and "Document:" line
    return re.split(r"(?<=\.)\s", body.strip(), maxsplit=1)[0]


def fake_call(schema, content, max_tokens=16000):
    prompt = content if isinstance(content, str) else content[-1]["text"]
    labels = LABELS.findall(prompt)
    good = _first_sentence(prompt, labels[0]) if labels else ""
    if schema is llm.AskAnswer or schema is llm.RFIAnswer:
        common = dict(
            spec_says=[
                llm.Quote(ref=labels[0], quote=good),                                   # genuine
                llm.Quote(ref=labels[0], quote="Bund walls shall be painted pink."),    # invented quote
                llm.Quote(ref="C99", quote=good),                                       # invented label
            ],
            interpretation=f"Applies as stated [{labels[0]}]; see also SUB-03-034 clause 99.9 and [C77].",
            gaps_conflicts=["None"], coverage="covered", likely_standard="",
        )
        if schema is llm.AskAnswer:
            return llm.AskAnswer(answer=f"Requirement per [{labels[0]}].", **common)
        return llm.RFIAnswer(rfi_summary="Asks X.", position="Non-compliant", position_basis=f"[{labels[0]}]",
                             draft_response=f"Not accepted [{labels[0]}], [C55].", **common)
    if schema is llm.ReviewBatch:
        ids = [int(i) for i in re.findall(r'<statement id="(\d+)"', prompt)]
        findings = []
        for n, sid in enumerate(ids):
            if n % 3 == 0:
                findings.append(llm.Finding(statement_id=sid, refs=[labels[0]], quote=good, finding="ok", rag="Green", comment="ok"))
            elif n % 3 == 1:
                findings.append(llm.Finding(statement_id=sid, refs=["C98"], quote="made up", finding="x", rag="Red", comment="x"))
            else:
                findings.append(llm.Finding(statement_id=sid, refs=[labels[0]], quote="Fabricated requirement text.",
                                            finding="x", rag="Red", comment="x"))
        return llm.ReviewBatch(findings=findings)
    if schema is llm.Extraction:
        return llm.Extraction(document_kind="drawing", title_block="DRG-1 P01", statements=[
            llm.ExtractedStatement(location="note 4", statement="BUND WALL THICKNESS 200mm.", topic="bund wall thickness"),
            llm.ExtractedStatement(location="note 5", statement="BUND CAPACITY 110%.", topic="bund capacity"),
            llm.ExtractedStatement(location="note 9", statement="GALVANISING 70 MICRONS.", topic="galvanising thickness"),
        ])
    if schema is llm.MissingNotes:
        return llm.MissingNotes(items=[
            llm.MissingNote(requirement="genuine", ref=labels[0], quote=good, status="Missing"),
            llm.MissingNote(requirement="invented", ref="C90", quote="nothing", status="Missing"),
        ])
    raise AssertionError(schema)


@pytest.fixture
def live_fake(monkeypatch):
    monkeypatch.setattr(llm, "mode", lambda: "live")
    monkeypatch.setattr(llm, "call", fake_call)


def _assert_all_real(conn, cits):
    for c in cits:
        assert check_citation(conn, c), f"citation not in database: {c}"


@pytest.mark.parametrize("fn,text", [
    (modes.ask, "What capacity must a transformer bund hold?"),
    (modes.rfi, "We propose 200mm bund walls sized for 110% of oil volume."),
])
def test_answers_only_cite_real_clauses(conn, live_fake, fn, text):
    ans = fn(text, SCOPE)
    assert ans.quotes, "the genuine quote should survive"
    for q in ans.quotes:
        assert check_citation(conn, q.clause.citation)
        assert quote_in_clause(q.quote, q.clause)
    _assert_all_real(conn, ans.cited)
    kinds = [r.kind for r in ans.rejected]
    assert "not_verbatim" in kinds and "unknown_label" in kinds and "unknown_clause" in kinds
    rendered = " ".join([ans.answer, ans.interpretation, ans.position_basis, ans.draft_response])
    for cit in citations.CITATION.finditer(rendered):
        assert check_citation(conn, cit.group(0))
    assert "[C77]" not in rendered and "[C55]" not in rendered
    assert "clause 99.9 [not found in library]" in ans.interpretation


def test_logged_citations_exist(conn, live_fake):
    modes.ask("Minimum ground bearing capacity for foundations?", SCOPE)
    import json

    entry = store.query_log(conn, 1)[0]
    cited = json.loads(entry["cited"])
    assert cited
    _assert_all_real(conn, cited)
    assert json.loads(entry["rejected"])


def test_review_rows_only_cite_real_clauses(conn, live_fake):
    rev = modes.review("drawing.txt", b"GENERAL NOTES\n1. BUND WALL THICKNESS 200mm.\n2. BUND CAPACITY 110%.", SCOPE)
    assert len(rev.rows) == 3
    for r in rev.rows:
        _assert_all_real(conn, r.citations)
        if r.quote:
            assert r.quote_verified
    # Row 2 cited a non-existent label; row 3 an invented quote → neither may stay Green/Red unverified.
    assert rev.rows[1].citations == [] and rev.rows[1].rag == "Amber"
    assert rev.rows[2].quote == "" and rev.rows[2].rag == "Amber"
    assert [m.requirement for m in rev.missing] == ["genuine"]
    _assert_all_real(conn, [m.citation for m in rev.missing])


def test_offline_mode_quotes_are_verbatim(conn):
    ans = modes.ask("What capacity must transformer oil containment bunds hold?", SCOPE)
    assert ans.offline and ans.quotes
    for q in ans.quotes:
        assert check_citation(conn, q.clause.citation)
        assert normalised_in(q.quote, q.clause.text)


def normalised_in(quote, text):
    return citations.normalise(quote) in citations.normalise(text)


def test_search_hits_exist(conn):
    for q in ["bund", "palisade fence pales", "C32/40", "surface water 1:25 return period"]:
        for h in search.search(q, 8, SCOPE, conn):
            assert check_citation(conn, h.clause.citation)


def test_verifier_tolerates_typography_only(conn):
    c = store.find_clause(conn, "SUB-03-034", "12.9.1")
    v = Verifier([c], conn)
    assert v.quote("C1", "The inner face of bund walls shall not be less than 1m clear on plan of oil containing parts.")
    assert v.quote("C1", "Bund layout shall be such that, as far as is reasonably practical, any 'spigot' or jetting' type flow is retained")
    assert v.quote("C1", "The inner face of bund walls shall not be less than 2m clear on plan") is None
    assert not check_citation(conn, "[SUB-03-034, Issue 5, Clause 12.9.9, p.29]")
    assert not check_citation(conn, "[SUB-03-034, Issue 4, Clause 12.9.1, pp.29–30]")
    assert check_citation(conn, c.citation)


def test_unknown_terms_reported(conn):
    ans = modes.ask("Is C40/50 concrete required for bund walls?", SCOPE)
    assert any("C40/50" in g for g in ans.gaps_conflicts)
