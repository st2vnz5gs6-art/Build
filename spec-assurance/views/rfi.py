import streamlit as st

from spec_assurance import export, modes, ui

ui.setup("RFI")
st.title("RFI")
st.caption("Paste an RFI. The tool takes a compliance position, cites the clauses that decide it and drafts response wording for you to edit.")

EXAMPLE = (
    "RFI-EGL1-CIV-047 – Transformer bund, Torness 400kV compound\n\n"
    "To suit the precast supplier's standard units we propose: (a) bund walls 200mm thick precast reinforced concrete; "
    "(b) bund volume of 110% of the transformer oil volume; (c) C28/35 concrete for the bund walls; and (d) a 100mm "
    "cable duct through the bund wall, sealed with a proprietary fire-rated sealant. Please confirm this is acceptable."
)

st.session_state.setdefault("rfi_text", "")
if st.button("Load example RFI", type="tertiary"):
    st.session_state["rfi_text"] = EXAMPLE
text = st.text_area("RFI text", key="rfi_text", height=180)
if st.button("Assess RFI", type="primary"):
    if not text.strip():
        st.warning("Paste the RFI text first.")
        st.stop()
    with st.spinner("Searching the library and assessing the RFI…"):
        st.session_state["rfi_result"] = modes.rfi(text.strip(), ui.doc_ids())

ans: modes.Answer | None = st.session_state.get("rfi_result")
if ans:
    st.divider()
    pos_cls = ui.POSITION_BADGE.get(ans.position, "b-grey")
    st.markdown(ui.badge(ans.position or "—", pos_cls) + ui.coverage_badge(ans), unsafe_allow_html=True)
    if ans.error:
        st.warning(ans.error)
    if ans.rfi_summary:
        ui.section("RFI asks")
        st.markdown(ans.rfi_summary)
    ui.section("Basis of position")
    st.markdown(ui.cited_label_text(ans.position_basis or "—"))
    ui.render_quotes(ans, "rfi")
    if ans.interpretation:
        ui.section("Interpretation (the tool's reading — not specification text)")
        st.markdown(ui.cited_label_text(ans.interpretation))
    ui.render_gaps(ans)
    if ans.draft_response:
        ui.section("Draft response (edit before issue)")
        ans.draft_response = st.text_area("Draft response", ans.draft_response, height=220,
                                          label_visibility="collapsed", key=f"rfi_draft_{id(ans)}")
    ui.render_rejected(ans.rejected)
    ui.render_retrieved(ans, "rfi")
    c1, c2, _ = st.columns([1, 1, 4])
    c1.download_button("Word", export.answer_to_docx(ans, ui.reviewer(), ui.project()), "rfi_response.docx",
                       icon=":material/description:")
    c2.download_button("PDF", export.html_to_pdf(export.answer_html(ans, ui.reviewer(), ui.project())), "rfi_response.pdf",
                       icon=":material/picture_as_pdf:")
