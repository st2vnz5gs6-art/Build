import streamlit as st

from spec_assurance import config, library, store, ui

ui.setup("Home")

# First run: index whatever is in /library so setup needs no extra command.
with store.session() as conn:
    empty = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0] == 0
if empty and any(p.suffix.lower() in library.SUPPORTED for p in config.LIBRARY_DIR.glob("*")):
    bar = st.progress(0.0, "First run: indexing the specification library…")
    library.reindex(progress=lambda f, m: bar.progress(min(f, 1.0), m))
    bar.empty()
    st.rerun()

st.markdown(
    """<div class="sa-hero"><h1>SPT Spec Assurance</h1>
    <p>Evidence-based answers to civil &amp; structural specification queries, RFIs and document reviews —
    every requirement traced to the exact clause of the SP Energy Networks specification it comes from.</p></div>""",
    unsafe_allow_html=True,
)

with store.session() as conn:
    docs = store.documents(conn)
    n_clauses = conn.execute("SELECT COUNT(*) FROM clauses").fetchone()[0]
    n_queries = conn.execute("SELECT COUNT(*) FROM query_log").fetchone()[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Specifications in library", len(docs))
c2.metric("Clauses indexed", f"{n_clauses:,}")
c3.metric("Pages parsed", sum(d["pages"] or 0 for d in docs))
c4.metric("Queries logged", n_queries)

if not docs:
    st.warning("The library is empty. Open **Library** and press **Re-index library** to ingest the PDFs in /library.")

st.markdown("#### Three ways to use it")
cols = st.columns(3)
cards = [
    ("views/ask.py", "Ask", "Free-text question. Get a direct answer, the verbatim clause text it rests on, "
     "the tool's interpretation and any gaps, kept separate."),
    ("views/rfi.py", "RFI", "Paste a contractor RFI. Get a compliance position — Compliant, Non-compliant or "
     "Clarification needed — with clause references and draft response wording."),
    ("views/review.py", "Document review", "Upload a report, calculation, design statement or drawing. Every "
     "technical statement or note is checked against the library in a RAG compliance table, exportable to Excel and Word."),
]
for col, (page, title, text) in zip(cols, cards):
    with col:
        st.markdown(f'<div class="sa-card"><h4>{title}</h4><p>{text}</p></div>', unsafe_allow_html=True)
        st.page_link(page, label=f"Open {title}", icon=":material/arrow_forward:")

st.markdown("#### How it stays trustworthy")
t1, t2, t3 = st.columns(3)
t1.markdown("**Clause-level library.** Each specification is parsed clause by clause — document, revision, clause "
            "number, heading, page — so every citation points to one place.")
t2.markdown("**Hybrid search.** Exact-term keyword search (grades, standards, dimensions) is combined with semantic "
            "search, and the retrieved clauses are always shown next to the answer.")
t3.markdown("**Citation verifier.** Every clause reference and quote in an answer is checked against the database. "
            "Anything that does not match is removed and reported — not shown as fact.")

if docs:
    st.markdown("#### Library")
    st.dataframe(
        [{"Document": d["doc_id"], "Title": d["title"].title() if d["title"].isupper() else d["title"],
          "Revision": d["revision"], "Clauses": d["clause_count"], "Precedence tier": d["tier"]} for d in docs],
        hide_index=True, use_container_width=True,
    )
