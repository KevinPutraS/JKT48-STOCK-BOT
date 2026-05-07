import os
import json
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="JKT48 Dashboard",
    layout="wide"
)

CACHE_FILE = "stock_cache.json"


def load_cache():

    if not os.path.exists(CACHE_FILE):
        return {}

    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


data = load_cache()

rows = []

for key, quota in data.items():

    parts = key.split("|||")

    category = parts[0] if len(parts) > 0 else "EVENT"

    event_code = parts[1] if len(parts) > 1 else "UNKNOWN"

    member = parts[2] if len(parts) > 2 else "UNKNOWN"

    session = parts[3] if len(parts) > 3 else "UNKNOWN"

    rows.append({
        "Category": category,
        "Member": member,
        "Session": session,
        "Stock": quota
    })

df = pd.DataFrame(rows)

st.title("🚀 JKT48 STOCK DASHBOARD")

# SEARCH
search = st.text_input("Cari Member")

# FILTER CATEGORY
categories = ["ALL"] + sorted(df["Category"].unique())

selected_category = st.selectbox(
    "Filter Category",
    categories
)

# FILTER MEMBER
members = ["ALL"] + sorted(df["Member"].unique())

selected_member = st.selectbox(
    "Filter Member",
    members
)

filtered = df.copy()

if search:
    filtered = filtered[
        filtered["Member"]
        .str.contains(search, case=False)
    ]

if selected_category != "ALL":
    filtered = filtered[
        filtered["Category"] == selected_category
    ]

if selected_member != "ALL":
    filtered = filtered[
        filtered["Member"] == selected_member
    ]

st.dataframe(
    filtered,
    use_container_width=True
)

# STATS
col1, col2, col3 = st.columns(3)

col1.metric(
    "Total Data",
    len(filtered)
)

col2.metric(
    "Total Member",
    filtered["Member"].nunique()
)

col3.metric(
    "Sold Out",
    len(filtered[filtered["Stock"] == 0])
)

# AUTO REFRESH
st.caption("Realtime refresh setiap reload")