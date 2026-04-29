import streamlit as st
import pandas as pd

st.set_page_config(page_title="Data Processing Tool", layout="wide")
st.title("📊 Data Processing Tool")

# ---------- Helpers ----------
def load_file(file):
    if file.name.endswith(('xls', 'xlsx')):
        return pd.read_excel(file)
    return pd.read_csv(file)

def clean_columns(df):
    df.columns = df.columns.str.strip()
    return df

# ---------- Upload ----------
file1 = st.file_uploader("Upload AMD Main File", type=["xls", "xlsx", "csv"])
file2 = st.file_uploader("Upload Daily BP Alert File", type=["xls", "xlsx", "csv"])

if file1 and file2:
    df_amd = clean_columns(load_file(file1))
    df_bp = clean_columns(load_file(file2))

    # ---------- Preview ----------
    st.subheader("🔍 AMD Main File Preview")
    st.dataframe(df_amd.head())

    st.subheader("🔍 BP Alert File Preview")
    st.dataframe(df_bp.head())

    # ---------- Manual Filter FIRST ----------
    st.subheader("🔎 Optional: Filter AMD by Battery Serial Numbers")

    manual_input = st.text_area(
        "Enter BP Serial Numbers (comma or line separated)",
        placeholder="ABC123\nXYZ456\nOR\nABC123, XYZ456"
    )

    if 'BP Serial Number' not in df_amd.columns:
        st.error("Column 'BP Serial Number' not found in AMD file")
        st.stop()

    if manual_input:
        serial_list = [x.strip() for x in manual_input.replace('\n', ',').split(',') if x.strip()]
        df_amd = df_amd[df_amd['BP Serial Number'].isin(serial_list)]

    # ---------- Column Selection ----------
    st.subheader("⚙️ Select Columns from AMD File")

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

    selected_cols = st.multiselect(
        "Choose columns",
        options=df_amd.columns,
        default=[col for col in default_cols if col in df_amd.columns]
    )

    if not selected_cols:
        st.warning("Please select at least one column")
        st.stop()

    df_amd = df_amd[selected_cols]

    # ---------- Validation ----------
    if 'BatterySerialNumber' not in df_bp.columns:
        st.error("Column 'BatterySerialNumber' not found in BP file")
        st.stop()

    # ---------- Matching ----------
    df_filtered = df_amd[df_amd['BP Serial Number'].isin(df_bp['BatterySerialNumber'])]

    # ---------- Remove duplicates ----------
    df_filtered = df_filtered.drop_duplicates()

    # ---------- Metrics ----------
    col1, col2, col3 = st.columns(3)
    col1.metric("AMD Records After Filter", len(df_amd))
    col2.metric("Matched Records", len(df_filtered))
    col3.metric("Unique Batteries", df_filtered['BP Serial Number'].nunique())

    # ---------- Zone Filter ----------
    if 'Zone Subzone Type' in df_filtered.columns:
        zone_filter = st.multiselect(
            "📍 Filter by Zone",
            options=df_filtered['Zone Subzone Type'].dropna().unique()
        )
        if zone_filter:
            df_filtered = df_filtered[df_filtered['Zone Subzone Type'].isin(zone_filter)]

    # ---------- Output ----------
    st.subheader("✅ Processed Data")
    st.dataframe(df_filtered)

    csv = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        "⬇️ Download Processed CSV",
        data=csv,
        file_name="processed_data.csv",
        mime="text/csv"
    )