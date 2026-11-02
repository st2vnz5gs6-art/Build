import json

import pandas as pd
import streamlit as st

from spec_assurance import store, ui

ui.setup("Audit log")
st.title("Audit log")
st.caption("Every question, RFI and review: what was asked, what was answered, which clauses were cited and any citations the verifier rejected.")

with store.session() as conn:
    rows = store.query_log(conn)
if not rows:
    st.info("Nothing logged yet.")
    st.stop()

df = pd.DataFrame([{
    "Time (UTC)": r["ts"], "Mode": r["mode"].upper(), "Query": r["query"],
    "Clauses cited": "\n".join(json.loads(r["cited"])), "Rejected": len(json.loads(r["rejected"])), "Model": r["model"],
} for r in rows])
mode = st.multiselect("Mode", sorted(df["Mode"].unique()), default=sorted(df["Mode"].unique()))
view = df[df["Mode"].isin(mode)]
st.dataframe(view, hide_index=True, use_container_width=True,
             column_config={"Query": st.column_config.TextColumn(width="large")})
st.download_button("Download log (CSV)", view.to_csv(index=False).encode("utf-8"), "spec_assurance_log.csv",
                   icon=":material/download:")

with st.expander("Full record"):
    idx = st.number_input("Entry", min_value=0, max_value=len(rows) - 1, value=0, help="0 = most recent")
    st.json(json.loads(rows[int(idx)]["answer_json"]))
