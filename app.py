import os
import json
import pandas as pd
import streamlit as st

from streamlit_autorefresh import st_autorefresh

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="JKT48 Dashboard",
    page_icon="🚀",
    layout="wide"
)

# =====================================================
# AUTO REFRESH
# =====================================================

st_autorefresh(
    interval=3000,
    key="refresh"
)

# =====================================================
# FILE
# =====================================================

CACHE_FILE = "stock_cache.json"

# =====================================================
# LOAD CACHE
# =====================================================

def load_cache():

    if not os.path.exists(CACHE_FILE):
        return {}

    try:

        with open(
            CACHE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except:
        return {}

# =====================================================
# DATA
# =====================================================

data = load_cache()

rows = []

for key, quota in data.items():

    parts = key.split("|||")

    category = (
        parts[0]
        if len(parts) > 0
        else "EVENT"
    )

    event_code = (
        parts[1]
        if len(parts) > 1
        else "UNKNOWN"
    )

    member = (
        parts[2]
        if len(parts) > 2
        else "UNKNOWN"
    )

    session = (
        parts[3]
        if len(parts) > 3
        else "UNKNOWN"
    )

    rows.append({

        "Category": category,
        "Event": event_code,
        "Member": member,
        "Session": session,
        "Stock": quota

    })

df = pd.DataFrame(rows)

if df.empty:

    st.warning("Stock cache kosong.")
    st.stop()

# =====================================================
# CSS
# =====================================================

st.markdown("""

<style>

.stApp{
    background:
        linear-gradient(
            135deg,
            #020617,
            #0f172a
        );
}

.block-container{
    padding-top:2rem;
}

h1,h2,h3,h4,h5,h6,p,label{
    color:white !important;
}

section[data-testid="stSidebar"]{
    background:#0f172a;
    border-right:1px solid #1e293b;
}

[data-testid="stMetric"]{
    background:
        linear-gradient(
            145deg,
            #111827,
            #1e293b
        );

    border:1px solid #1f2937;

    padding:18px;

    border-radius:22px;

    text-align:center;

    box-shadow:
        0 10px 30px rgba(0,0,0,0.25);
}

[data-testid="stMetricValue"]{
    font-size:42px;
}

[data-testid="stDataFrame"]{
    border-radius:20px;
    overflow:hidden;
    border:1px solid #1f2937;
}

</style>

""", unsafe_allow_html=True)

# =====================================================
# HEADER
# =====================================================

st.title("🚀 JKT48 REALTIME DASHBOARD")

st.caption(
    "Live stock monitoring realtime"
)

st.success(
    "🟢 LIVE MONITORING ACTIVE"
)

# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.title("⭐ Priority Member")

pinned = st.sidebar.multiselect(
    "Pinned Member",
    sorted(df["Member"].unique())
)

st.sidebar.markdown("---")

auto_low = st.sidebar.toggle(
    "⚠️ Show Low Stock Only",
    value=False
)

sold_only = st.sidebar.toggle(
    "❌ Show Sold Out Only",
    value=False
)

# =====================================================
# FILTERS
# =====================================================

col1, col2, col3 = st.columns(3)

with col1:

    search = st.text_input(
        "🔍 Cari Member"
    )

with col2:

    categories = (
        ["ALL"]
        +
        sorted(df["Category"].unique())
    )

    selected_category = st.selectbox(
        "📁 Filter Category",
        categories
    )

with col3:

    members = (
        ["ALL"]
        +
        sorted(df["Member"].unique())
    )

    selected_member = st.selectbox(
        "⭐ Filter Member",
        members
    )

# =====================================================
# FILTER PROCESS
# =====================================================

filtered = df.copy()

if search:

    filtered = filtered[
        filtered["Member"]
        .str.contains(
            search,
            case=False
        )
    ]

if selected_category != "ALL":

    filtered = filtered[
        filtered["Category"]
        ==
        selected_category
    ]

if selected_member != "ALL":

    filtered = filtered[
        filtered["Member"]
        ==
        selected_member
    ]

if pinned:

    filtered = filtered[
        filtered["Member"]
        .isin(pinned)
    ]

if auto_low:

    filtered = filtered[
        filtered["Stock"] <= 2
    ]

if sold_only:

    filtered = filtered[
        filtered["Stock"] == 0
    ]

# =====================================================
# SORT
# =====================================================

filtered = filtered.sort_values(
    by="Stock",
    ascending=True
)

# =====================================================
# STATS
# =====================================================

available = len(
    filtered[
        filtered["Stock"] > 2
    ]
)

low_stock = len(
    filtered[
        (
            filtered["Stock"] > 0
        )
        &
        (
            filtered["Stock"] <= 2
        )
    ]
)

sold_out = len(
    filtered[
        filtered["Stock"] == 0
    ]
)

total_member = (
    filtered["Member"]
    .nunique()
)

# =====================================================
# METRICS
# =====================================================

m1, m2, m3, m4 = st.columns(4)

with m1:

    st.metric(
        "AVAILABLE",
        available
    )

with m2:

    st.metric(
        "LOW STOCK",
        low_stock
    )

with m3:

    st.metric(
        "SOLD OUT",
        sold_out
    )

with m4:

    st.metric(
        "TOTAL MEMBER",
        total_member
    )

# =====================================================
# CHART
# =====================================================

st.markdown("## 📊 Stock Distribution")

chart_data = pd.DataFrame({

    "Status":[
        "Available",
        "Low Stock",
        "Sold Out"
    ],

    "Count":[
        available,
        low_stock,
        sold_out
    ]

})

st.bar_chart(
    chart_data.set_index("Status")
)

# =====================================================
# TABLE STYLE
# =====================================================

def color_stock(val):

    if val == 0:

        return (
            "color:#ef4444;"
            "font-weight:bold;"
        )

    elif val <= 2:

        return (
            "color:#f59e0b;"
            "font-weight:bold;"
        )

    return (
        "color:#22c55e;"
        "font-weight:bold;"
    )

styled_df = filtered.style.map(
    color_stock,
    subset=["Stock"]
)

# =====================================================
# TABS
# =====================================================

tab1, tab2 = st.tabs([
    "📋 Dashboard",
    "📈 Analytics"
])

# =====================================================
# TAB 1
# =====================================================

with tab1:

    st.subheader("📋 Live Stock Table")

    st.dataframe(
        styled_df,
        use_container_width=True,
        height=650
    )

    csv = filtered.to_csv(
        index=False
    )

    st.download_button(
        "📥 Download CSV",
        csv,
        "jkt48_stock.csv",
        "text/csv"
    )

# =====================================================
# TAB 2
# =====================================================

with tab2:

    st.subheader("📈 Top Member Stock")

    top_member = (
        filtered
        .groupby("Member")["Stock"]
        .sum()
        .sort_values(
            ascending=False
        )
        .head(10)
    )

    st.bar_chart(top_member)

    st.subheader("📁 Category Distribution")

    category_chart = (
        filtered
        .groupby("Category")["Stock"]
        .sum()
    )

    st.bar_chart(category_chart)

# =====================================================
# FOOTER
# =====================================================

st.caption(
    "🟢 Auto refresh every 3 seconds"
)