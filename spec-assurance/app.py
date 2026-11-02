"""SPT Spec Assurance — Streamlit entry point.  Run:  streamlit run app.py"""

import streamlit as st

st.set_page_config(page_title="SPT Spec Assurance", page_icon="📐", layout="wide")

pages = [
    st.Page("views/home.py", title="Home", icon=":material/home:", default=True),
    st.Page("views/ask.py", title="Ask", icon=":material/help:"),
    st.Page("views/rfi.py", title="RFI", icon=":material/mail:"),
    st.Page("views/review.py", title="Document review", icon=":material/fact_check:"),
    st.Page("views/library.py", title="Library", icon=":material/library_books:"),
    st.Page("views/log.py", title="Audit log", icon=":material/history:"),
]
st.navigation(pages).run()
