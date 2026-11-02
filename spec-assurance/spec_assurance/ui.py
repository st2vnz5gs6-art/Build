"""Shared Streamlit components: styling, sidebar settings, clause viewer, answer rendering."""

from __future__ import annotations

import html
import re

import pymupdf
import streamlit as st

from . import config, hierarchy, llm, store
from .modes import Answer
from .store import ClauseRow

CSS = """
<style>
:root { --navy:#1F3864; --teal:#00747A; --muted:#5f6b7a; }
.block-container { padding-top: 2.2rem; max-width: 1250px; }
h1, h2, h3 { color: var(--navy); letter-spacing: -0.01em; }
.sa-hero { padding: 1.4rem 1.6rem; border-radius: 10px; background: linear-gradient(120deg,#1F3864 0%,#2c4f86 60%,#00747A 100%); color:#fff; margin-bottom: 1.2rem; }
.sa-hero h1 { color:#fff; margin:0 0 .3rem 0; font-size: 2rem; }
.sa-hero p { margin:0; opacity:.92; font-size:1.02rem; }
.sa-card { border:1px solid #dde3ea; border-radius:10px; padding:1rem 1.1rem; height:100%; background:#fff; }
.sa-card h4 { margin:.1rem 0 .4rem 0; color:var(--navy); }
.sa-card p { color:#33404f; font-size:.93rem; margin:0; }
.sa-badge { display:inline-block; padding:.18rem .6rem; border-radius:999px; font-weight:600; font-size:.82rem; margin-right:.35rem; }
.b-green { background:#C6EFCE; color:#0b5d1e; } .b-amber { background:#FFEB9C; color:#7a5a00; }
.b-red { background:#FFC7CE; color:#8a0f1f; } .b-grey { background:#e4e7eb; color:#3b4652; }
.b-blue { background:#dbe7f6; color:#1F3864; }
.sa-quote { border-left:4px solid var(--teal); background:#f4f8f9; padding:.6rem .9rem; margin:.25rem 0 .2rem 0; border-radius:0 6px 6px 0; font-size:.95rem; }
.sa-cite { font-family: ui-monospace, Consolas, monospace; font-size:.82rem; color:var(--navy); font-weight:600; }
.sa-section { font-size:.78rem; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); font-weight:700; margin:1.1rem 0 .35rem 0; }
.sa-note { color:var(--muted); font-size:.85rem; }
mark { background:#ffe58a; padding:0 .1rem; }
button[data-testid="stBaseButton-tertiary"] p { font-family: ui-monospace, Consolas, monospace; font-size:.84rem;
  color:#1F3864; font-weight:600; text-decoration: underline dotted; }
button[data-testid="stBaseButton-tertiary"]:hover p { color:#00747A; }
</style>
"""

COVERAGE_BADGE = {"covered": ("Covered by library", "b-green"), "partial": ("Partly covered", "b-amber"),
                  "not_covered": ("Not covered by the library", "b-red")}
POSITION_BADGE = {"Compliant": "b-green", "Non-compliant": "b-red", "Clarification needed": "b-amber"}
RAG_BADGE = {"Green": "b-green", "Amber": "b-amber", "Red": "b-red", "Not covered": "b-grey", "Not assessed": "b-grey",
             "Missing": "b-red", "Present": "b-green", "Unclear": "b-amber"}


def setup(title: str) -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    sidebar()


def badge(text: str, cls: str) -> str:
    return f'<span class="sa-badge {cls}">{html.escape(text)}</span>'


def section(label: str) -> None:
    st.markdown(f'<div class="sa-section">{html.escape(label)}</div>', unsafe_allow_html=True)


def sidebar() -> None:
    with st.sidebar:
        st.markdown("### Settings")
        presets = hierarchy.scope_presets()
        with store.session() as conn:
            docs = [d["doc_id"] for d in store.documents(conn)]
        names = list(presets)
        st.session_state.setdefault("scope", names[0])
        st.selectbox("Asset type / document scope", names, key="scope",
                     help="Limits searches to the specifications that apply. Policies (SUB-01) apply to all voltages.")
        chosen = presets[st.session_state["scope"]] or docs
        st.session_state["doc_ids"] = [d for d in chosen if d in docs] or docs
        with st.expander("Documents in scope", expanded=False):
            st.write(", ".join(st.session_state["doc_ids"]) or "Library is empty")
        st.text_input("Reviewer name (for exports)", key="reviewer")
        st.text_input("Project", value="Eastern Green Link 1 (EGL1)", key="project")
        st.divider()
        if llm.mode() == "live":
            st.markdown(badge("Claude connected", "b-green") + f'<div class="sa-note">Model: {config.CLAUDE_MODEL}</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(badge("Offline mode", "b-amber") +
                        '<div class="sa-note">No API key: search and clause evidence only. Add ANTHROPIC_API_KEY to .env.</div>',
                        unsafe_allow_html=True)
        st.markdown('<div class="sa-note" style="margin-top:.8rem">Documents stay on this machine. Only the retrieved '
                    'clauses and your query are sent to the Claude API.</div>', unsafe_allow_html=True)


def doc_ids() -> list[str]:
    return st.session_state.get("doc_ids") or []


def reviewer() -> str:
    return st.session_state.get("reviewer", "")


def project() -> str:
    return st.session_state.get("project", "")


# --------------------------------------------------------------------------- clause viewer

def _highlight(text: str, quote: str) -> str:
    esc = html.escape(text)
    if not quote:
        return esc
    words = [re.escape(html.escape(w)) for w in quote.split()[:12]]
    if not words:
        return esc
    pat = re.compile(r"\s+".join(words), re.I)
    m = pat.search(esc)
    if not m:
        return esc
    # The match covers the quote's opening words; extend it by the quote's length.
    end = min(len(esc), max(m.end(), m.start() + len(html.escape(quote))))
    return esc[: m.start()] + "<mark>" + esc[m.start(): end] + "</mark>" + esc[end:]


@st.cache_data(show_spinner=False, max_entries=64)
def page_image(filename: str, page_no: int, quote: str) -> bytes | None:
    path = config.LIBRARY_DIR / filename
    if not path.exists() or path.suffix.lower() != ".pdf":
        return None
    doc = pymupdf.open(str(path))
    if not (1 <= page_no <= doc.page_count):
        return None
    page = doc[page_no - 1]
    if quote:
        # Search the quote in short runs of words (PDF line breaks split longer phrases).
        words = quote.split()
        for i in range(0, len(words), 5):
            frag = " ".join(words[i:i + 5])
            if len(frag) > 8:
                for r in page.search_for(frag):
                    page.add_highlight_annot(r)
    return page.get_pixmap(dpi=110).tobytes("png")


@st.dialog("Source clause", width="large")
def clause_dialog(clause_id: int, quote: str = "") -> None:
    with store.session() as conn:
        rows = store.get_clauses(conn, [clause_id])
        fn = conn.execute("SELECT filename FROM documents WHERE doc_id = ?", (rows[0].doc_id,)).fetchone() if rows else None
    if not rows:
        st.error("Clause not found.")
        return
    c = rows[0]
    st.markdown(f'<span class="sa-cite">{html.escape(c.citation)}</span>', unsafe_allow_html=True)
    st.markdown(f"**{c.clause_no} {c.heading}**  \n<span class='sa-note'>{html.escape(c.title)} · {html.escape(c.path)}</span>",
                unsafe_allow_html=True)
    tab_text, tab_page = st.tabs(["Clause text", "Source page"])
    with tab_text:
        body = _highlight(c.text, quote).replace("\n", "<br/>")
        st.markdown(f'<div style="font-size:.93rem;line-height:1.5">{body}</div>', unsafe_allow_html=True)
    with tab_page:
        if fn and c.page_start:
            pages = list(range(c.page_start, (c.page_end or c.page_start) + 1))
            p = st.radio("Page", pages, horizontal=True, label_visibility="collapsed") if len(pages) > 1 else pages[0]
            img = page_image(fn[0], p, quote)
            if img:
                st.image(img, use_container_width=True, caption=f"{c.doc_id} page {p} (quote highlighted where found)")
        else:
            st.info("No page image for this document.")


def citation_button(c: ClauseRow, quote: str, key: str) -> None:
    if st.button(c.citation, key=key, type="tertiary", help="Open the source clause"):
        clause_dialog(c.id, quote)


# --------------------------------------------------------------------------- answer rendering

def render_quotes(ans: Answer, key: str) -> None:
    section("What the specification says")
    if not ans.quotes:
        st.markdown('<div class="sa-note">No verified quote. Nothing from the library supports a requirement here.</div>',
                    unsafe_allow_html=True)
    for i, q in enumerate(ans.quotes):
        citation_button(q.clause, q.quote, f"{key}-q{i}")
        st.markdown(f'<div class="sa-quote">“{html.escape(q.quote)}”</div>', unsafe_allow_html=True)


def render_gaps(ans: Answer) -> None:
    items = list(ans.gaps_conflicts)
    if ans.likely_standard:
        items.append(f"Likely governing standard: {ans.likely_standard}")
    if items:
        section("Gaps and conflicts")
        for g in items:
            st.markdown(f"- {g}")


def render_rejected(rejected) -> None:
    if rejected:
        with st.expander(f"⚠ {len(rejected)} citation(s) removed by the verifier"):
            st.caption("The model cited something that could not be matched to the library. It has been removed from the answer.")
            for r in rejected:
                st.markdown(f"- **{r.kind.replace('_', ' ')}** – {r.detail}")


def render_retrieved(ans: Answer, key: str) -> None:
    with st.expander(f"Retrieved clauses ({len(ans.hits)}) — what the answer was based on"):
        for i, h in enumerate(ans.hits):
            cols = st.columns([5, 1])
            with cols[0]:
                citation_button(h.clause, "", f"{key}-r{i}")
                st.caption(f"{h.clause.heading} — {h.clause.path}")
            with cols[1]:
                st.caption(f"score {h.score:.2f}\nkeyword #{h.bm25_rank or '–'} · semantic #{h.vector_rank or '–'}")
            st.markdown(f"<div class='sa-note'>{html.escape(h.clause.text[:420])}{'…' if len(h.clause.text) > 420 else ''}</div>",
                        unsafe_allow_html=True)


def coverage_badge(ans: Answer) -> str:
    text, cls = COVERAGE_BADGE.get(ans.coverage, (ans.coverage, "b-grey"))
    out = badge(text, cls)
    if ans.offline:
        out += badge("Offline – not interpreted", "b-grey")
    return out


def cited_label_text(text: str) -> str:
    """Bold the inline citations the verifier inserted."""
    return re.sub(r"(\[[A-Z]{2,6}-\d{2}-\d{3}, [^\]]+\])", r"**\1**", text)

