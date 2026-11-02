import streamlit as st

from spec_assurance import config, library, store, ui

ui.setup("Library")
st.title("Library")
st.caption(f"Specifications are read from `{config.LIBRARY_DIR}`. Drop PDF or DOCX files there, or upload below, then re-index.")

uploads = st.file_uploader("Add specifications", type=["pdf", "docx"], accept_multiple_files=True)
c1, c2, _ = st.columns([1, 1, 3])
add = c1.button("Add to library", disabled=not uploads)
reindex = c2.button("Re-index library", type="primary")
force = st.checkbox("Re-parse unchanged files too", value=False)

if add and uploads:
    for f in uploads:
        library.save_upload(f.name, f.getvalue())
    reindex = True

if reindex:
    bar = st.progress(0.0, "Starting")
    results = library.reindex(force=force, progress=lambda f, m: bar.progress(min(f, 1.0), m))
    bar.empty()
    for r in results:
        if r.status == "failed":
            st.error(f"{r.filename}: {r.message}")
    st.success(f"Indexed {sum(r.status == 'ingested' for r in results)} file(s), "
               f"{sum(r.status == 'unchanged' for r in results)} unchanged.")

with store.session() as conn:
    docs = store.documents(conn)

if not docs:
    st.info("No documents indexed yet.")
    st.stop()

st.dataframe(
    [{"Document": d["doc_id"], "Title": d["title"], "Revision": d["revision"], "Pages": d["pages"],
      "Clauses": d["clause_count"], "Precedence tier": d["tier"], "File": d["filename"],
      "Synthetic": "Yes" if d["synthetic"] else "", "Indexed": d["ingested_at"]} for d in docs],
    hide_index=True, use_container_width=True,
)

st.markdown("#### Browse clauses")
doc_id = st.selectbox("Document", [d["doc_id"] for d in docs],
                      format_func=lambda d: next(f"{x['doc_id']} — {x['title'][:80]}" for x in docs if x["doc_id"] == d))
with store.session() as conn:
    clauses = store.all_clauses(conn, doc_id)
flt = st.text_input("Filter by clause number or text", placeholder="e.g. 12.9 or bund")
shown = [c for c in clauses if not flt or flt.lower() in f"{c.clause_no} {c.heading} {c.text}".lower()]
st.caption(f"{len(shown)} of {len(clauses)} clauses")
st.dataframe(
    [{"Clause": c.clause_no, "Heading": c.heading, "Pages": c.pages.replace("p.", "").replace("pp.", ""),
      "Section": c.path, "Words": len(c.text.split())} for c in shown],
    hide_index=True, use_container_width=True, height=320,
)
pick = st.selectbox("Open clause", [c.clause_no for c in shown], format_func=lambda n: next(f"{c.clause_no} {c.heading}" for c in shown if c.clause_no == n)) if shown else None
if pick:
    c = next(c for c in shown if c.clause_no == pick)
    st.markdown(f'<span class="sa-cite">{c.citation}</span>', unsafe_allow_html=True)
    st.markdown(c.text.replace("\n", "  \n") or "_(heading only — see sub-clauses)_")
    if st.button("View source page", icon=":material/image:"):
        ui.clause_dialog(c.id)
