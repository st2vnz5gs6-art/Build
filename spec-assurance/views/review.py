import html
from pathlib import Path

import streamlit as st

from spec_assurance import export, llm, modes, ui
from spec_assurance.ingest import drawings

ui.setup("Document review")
st.title("Document review")
st.caption("Upload a contractor report, calculation, design statement or drawing. Each technical statement or drawing "
           "note is checked against the library. Drawings are checked for their text only — geometry is not assessed.")

DEMO_DIR = Path(__file__).resolve().parent.parent / "demo" / "inputs"
demo_files = sorted(p for p in DEMO_DIR.glob("*") if p.is_file()) if DEMO_DIR.exists() else []

up = st.file_uploader("Document to review", type=["pdf", "docx", "txt", "png", "jpg", "jpeg", "tif", "tiff"])
if demo_files:
    demo_pick = st.selectbox("…or use a demo submission", ["—"] + [p.name for p in demo_files])
else:
    demo_pick = "—"

source = None
if up is not None:
    source = (up.name, up.getvalue())
elif demo_pick != "—":
    source = (demo_pick, (DEMO_DIR / demo_pick).read_bytes())

ocr_note = "Tesseract OCR found" if drawings.tesseract_available() else (
    "Tesseract not installed — scanned drawings use Claude vision" if llm.mode() == "live" else
    "Tesseract not installed and offline — scanned drawings cannot be read")
st.markdown(f'<div class="sa-note">Scanned pages: {ocr_note}.</div>', unsafe_allow_html=True)

if st.button("Run review", type="primary", disabled=source is None):
    bar = st.progress(0.0, "Starting")
    st.session_state["review_result"] = modes.review(source[0], source[1], ui.doc_ids(),
                                                     progress=lambda f, m: bar.progress(min(f, 1.0), m))
    bar.empty()

rev: modes.Review | None = st.session_state.get("review_result")
if rev:
    st.divider()
    st.markdown(f"#### {html.escape(rev.filename)}")
    meta = [ui.badge(rev.document_kind.title(), "b-blue")]
    if rev.offline:
        meta.append(ui.badge("Offline – statements matched to clauses, not assessed", "b-grey"))
    st.markdown("".join(meta), unsafe_allow_html=True)
    if rev.title_block:
        st.markdown(f"**Title block:** {rev.title_block}")
    if rev.error:
        st.warning(rev.error)
    methods = sorted({p.method for p in rev.pages})
    st.caption(f"{len(rev.pages)} page(s) read via {', '.join(methods)} · {len(rev.rows)} statement(s) checked")

    counts = rev.rag_counts
    cols = st.columns(5)
    for col, key in zip(cols, ["Green", "Amber", "Red", "Not covered", "Not assessed"]):
        col.metric(key, counts.get(key, 0))

    ui.section("Compliance table")
    table = [{"No.": r.no, "Location": r.location, "Statement": r.statement, "Clause": "\n".join(r.citations),
              "Finding": r.finding, "RAG": r.rag, "Comment": r.comment} for r in rev.rows]

    def _rag_style(v):
        colours = {"Green": "#C6EFCE", "Amber": "#FFEB9C", "Red": "#FFC7CE", "Not covered": "#e4e7eb", "Not assessed": "#eef0f2"}
        return f"background-color: {colours.get(v, '')}"

    if table:
        import pandas as pd

        df = pd.DataFrame(table)
        st.dataframe(df.style.map(_rag_style, subset=["RAG"]), hide_index=True, use_container_width=True,
                     column_config={"Statement": st.column_config.TextColumn(width="large"),
                                    "Finding": st.column_config.TextColumn(width="large"),
                                    "Comment": st.column_config.TextColumn(width="large")})

    ui.section("Evidence by statement")
    for r in rev.rows:
        with st.expander(f"{r.no}. [{r.rag}] {r.statement[:110]}{'…' if len(r.statement) > 110 else ''}"):
            st.markdown(ui.badge(r.rag, ui.RAG_BADGE.get(r.rag, "b-grey")) + f" <span class='sa-note'>{html.escape(r.location)}</span>",
                        unsafe_allow_html=True)
            st.markdown(f"**Statement:** {r.statement}")
            st.markdown(f"**Finding:** {ui.cited_label_text(r.finding)}")
            if r.quote:
                st.markdown(f'<div class="sa-quote">“{html.escape(r.quote)}”</div>', unsafe_allow_html=True)
            if r.comment:
                st.markdown(f"**Comment:** {ui.cited_label_text(r.comment)}")
            if r.citations:
                st.caption("Clauses: " + " · ".join(r.citations))
            if r.candidates:
                st.caption("Candidate clauses searched: " + " · ".join(r.candidates))

    if rev.missing:
        ui.section("Notes the specifications require")
        for m in rev.missing:
            st.markdown(ui.badge(m.status, ui.RAG_BADGE.get(m.status, "b-grey")) + f" **{html.escape(m.requirement)}**  "
                        f"<span class='sa-cite'>{html.escape(m.citation)}</span>", unsafe_allow_html=True)
            st.markdown(f'<div class="sa-quote">“{html.escape(m.quote)}”</div>', unsafe_allow_html=True)

    ui.render_rejected(rev.rejected)

    with st.expander("Extracted text"):
        for p in rev.pages:
            st.caption(f"Page {p.page} — {p.method}")
            st.text(p.text[:6000])

    ui.section("Export")
    stem = Path(rev.filename).stem
    c1, c2, c3, _ = st.columns([1, 1, 1, 3])
    c1.download_button("Excel", export.review_to_excel(rev, ui.reviewer(), ui.project()), f"{stem}_compliance.xlsx",
                       icon=":material/table_view:")
    c2.download_button("Word", export.review_to_docx(rev, ui.reviewer(), ui.project()), f"{stem}_comment_sheet.docx",
                       icon=":material/description:")
    c3.download_button("PDF", export.html_to_pdf(export.review_html(rev, ui.reviewer(), ui.project()), landscape=True),
                       f"{stem}_comment_sheet.pdf", icon=":material/picture_as_pdf:")
