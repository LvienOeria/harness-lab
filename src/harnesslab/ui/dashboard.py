from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="harness-lab", layout="wide")
st.title("🧪 harness-lab")
st.caption("model × harness configuration evaluation for DeepSeek agents")

summary_path = Path("results-matrix/matrix-summary.json")
if not summary_path.exists():
    st.warning("No matrix results yet. Run: harness-lab run-matrix --tasks all")
    st.stop()

rows = json.loads(summary_path.read_text())
df = pd.DataFrame(rows)
st.metric("tasks", df["task"].nunique())
st.metric("cells", len(df))
st.metric("mean completion", f"{df['completion'].mean():.1%}")

st.subheader("Completion heatmap")
pivot = df.pivot_table(index="task", columns="runner", values="completion", aggfunc="mean")
st.dataframe(pivot, use_container_width=True)

st.subheader("Cost by runner")
fig = px.bar(df, x="task", y="total_cost_usd", color="runner", barmode="group")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Raw matrix")
st.dataframe(df, use_container_width=True)
