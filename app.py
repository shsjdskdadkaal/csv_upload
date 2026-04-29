import streamlit as st
import pandas as pd

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Indofast Battery Dashboard", layout="wide")

# ---------- CUSTOM THEME ----------
st.markdown("""
<style>
body {
    background-color: #0a0a0a;
    color: white;
}
.stApp {
    background-color: #0a0a0a;
}
h1, h2, h3 {
    color: #d4ff00;
}
.stButton>button {
    background-color: #d4ff00;
    color: black;
    border-radius: 8px;
}
.stDownloadButton>button {
    background-color: #d4ff00;
    color: black;
    border-radius: 8px;
}
.css-1d391kg, .css-1v0mbdj {
    background-color: #111111;
}
</style>
""", unsafe_allow_html=True)

# ---------- TITLE ----------
st.markdown("## ⚡ INDOFAST ENERGY - Battery Dashboard")

# ---------- HELPERS ----------
def load_file(file):
    if file.name.endswith(('xls', 'xlsx')):
        return pd.read_excel(file)
    return pd.read_csv(file)

def clean_columns(df):
    df.columns = df.columns.str.strip()
    return df

# ---------- SIDEBAR ----------
st.sidebar.header("⚙️ Controls")

file1 = st.sidebar.file_uploader("Upload AMD File (Required)", type=["xls", "xlsx", "csv"])
file2 = st.sidebar.file_uploader("Upload BP Alert File (Optional)", type=["xls", "xlsx", "csv"])

if not file1:
    st.info("👈 Upload AMD file to start")
    st.stop()

df_amd = clean_columns(load_file(file1))

# ---------- SERIAL FILTER ----------
st.sidebar.subheader("🔎 Battery Filter")

if 'BP Serial Number' not in df_amd.columns:
    st.error("Missing 'BP Serial Number'")
    st.stop()

manual_input = st.sidebar.text_area(
    "Enter Battery Serials",
    placeholder="ABC123, XYZ456"
)

if manual_input:
    serial_list = [x.strip() for x in manual_input.replace('\n', ',').split(',') if x.strip()]
    df_amd = df_amd[df_amd['BP Serial Number'].isin(serial_list)]

# ---------- ADVANCED FILTERS ----------
st.sidebar.subheader("📊 Advanced Filters")

filter_columns = st.sidebar.multiselect("Select Columns", df_amd.columns)

for col in filter_columns:
    unique_vals = df_amd[col].dropna().unique()

    if len(unique_vals) > 50:
        val = st.sidebar.text_input(f"{col} contains")
        if val:
            df_amd = df_amd[df_amd[col].astype(str).str.contains(val, case=False, na=False)]
    else:
        val = st.sidebar.multiselect(f"{col}", unique_vals)
        if val:
            df_amd = df_amd[df_amd[col].isin(val)]

# ---------- COLUMN SELECTION ----------
default_cols = [
    'BP Serial Number',
    'Zone Subzone Type',
    'Latest Transaction Date',
    'BP Last Seen In_Vehicle_VIN',
    'BP Last Seen In_Vehicle_Registration Number',
    'BP Last Seen In_Vehicle _Vehicle Type',
    'BP Last Seen In_Vehicle_Business Type',
    'BP Last Seen In_Vehicle_Customer Name'
]

selected_cols = st.sidebar.multiselect(
    "📌 Select Columns",
    options=df_amd.columns,
    default=[col for col in default_cols if col in df_amd.columns]
)

if selected_cols:
    df_amd = df_amd[selected_cols]

# ---------- MATCHING ----------
if file2:
    df_bp = clean_columns(load_file(file2))

    if 'BatterySerialNumber' not in df_bp.columns:
        st.error("Missing BatterySerialNumber in BP file")
        st.stop()

    df_final = df_amd[df_amd['BP Serial Number'].isin(df_bp['BatterySerialNumber'])]
    mode = "🔗 Matched with BP Alerts"
else:
    df_final = df_amd
    mode = "📄 AMD Only Mode"

df_final = df_final.drop_duplicates()

# ---------- KPIs ----------
st.markdown("### 📈 Key Metrics")

col1, col2, col3 = st.columns(3)

col1.metric("Total Records", len(df_amd))
col2.metric("Final Records", len(df_final))
col3.metric("Unique Batteries", df_final['BP Serial Number'].nunique())

st.caption(mode)

# ---------- COLUMN FILTERS ----------
st.markdown("### 🧩 Column Filters")

with st.expander("Apply Excel-style filters"):
    filter_df = df_final.copy()
    cols = st.columns(len(filter_df.columns))

    for i, col in enumerate(filter_df.columns):
        unique_vals = filter_df[col].dropna().unique()

        with cols[i]:
            if len(unique_vals) <= 20:
                selected = st.multiselect(col, unique_vals)
                if selected:
                    filter_df = filter_df[filter_df[col].isin(selected)]
            else:
                search = st.text_input(col, key=col)
                if search:
                    filter_df = filter_df[
                        filter_df[col].astype(str).str.contains(search, case=False, na=False)
                    ]

    df_final = filter_df

# ---------- DATA TABLE ----------
st.markdown("### 📋 Processed Data")

preview_df = df_final.head(1000)

st.dataframe(preview_df, use_container_width=True)

st.caption(f"Showing {len(preview_df)} of {len(df_final)} rows")

# ---------- DOWNLOAD ----------
csv = df_final.to_csv(index=False).encode('utf-8')

st.download_button(
    "⬇️ Download Full Data",
    data=csv,
    file_name="processed_data.csv",
    mime="text/csv"
)