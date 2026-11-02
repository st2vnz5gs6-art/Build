import streamlit as st

from spec_assurance import export, modes, ui

ui.setup("Ask")
st.title("Ask")
st.caption("Ask a question about the specifications. The answer quotes the clauses it relies on; anything the library does not cover is said plainly.")

EXAMPLES = [
    "What capacity must a transformer oil containment bund be designed to hold, and how thick must reinforced concrete bund walls be?",
    "What is the minimum concrete cover to reinforcement for transformer bund walls?",
    "What galvanising thickness is required for steelwork, and what are the requirements for equipment support base plates?",
    "What return periods must the surface water drainage be designed for?",
]

st.session_state.setdefault("ask_q", "")
cols = st.columns(len(EXAMPLES))
for i, (col, ex) in enumerate(zip(cols, EXAMPLES)):
    if col.button(ex[:58] + "…", key=f"ex{i}", use_container_width=True, help=ex):
        st.session_state["ask_q"] = ex

q = st.text_area("Question", key="ask_q", height=90, placeholder="e.g. What is the minimum ground bearing capacity for foundations?")
if st.button("Ask", type="primary"):
    if not q.strip():
        st.warning("Type a question first.")
        st.stop()
    with st.spinner("Searching the library and checking the evidence…"):
        st.session_state["ask_result"] = modes.ask(q.strip(), ui.doc_ids())

ans: modes.Answer | None = st.session_state.get("ask_result")
if ans:
    st.divider()
    st.markdown(ui.coverage_badge(ans), unsafe_allow_html=True)
    if ans.error:
        st.warning(ans.error)
    ui.section("Answer")
    st.markdown(ui.cited_label_text(ans.answer))
    ui.render_quotes(ans, "ask")
    if ans.interpretation:
        ui.section("Interpretation (the tool's reading — not specification text)")
        st.markdown(ui.cited_label_text(ans.interpretation))
    ui.render_gaps(ans)
    ui.render_rejected(ans.rejected)
    ui.render_retrieved(ans, "ask")
    c1, c2, _ = st.columns([1, 1, 4])
    c1.download_button("Word", export.answer_to_docx(ans, ui.reviewer(), ui.project()), "spec_query.docx",
                       icon=":material/description:")
    c2.download_button("PDF", export.html_to_pdf(export.answer_html(ans, ui.reviewer(), ui.project())), "spec_query.pdf",
                       icon=":material/picture_as_pdf:")
