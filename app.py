#%%
import streamlit as st
import pandas as pd
#%%
st.set_page_config(page_title="Data Processing Tool", layout="wide")
st.title("📊 Data Processing Tool")

file1 = st.file_uploader("Upload your AMD Main File", type=["xls", "xlsx", "csv"])
file2 = st.file_uploader("Upload your Daily BP Alert File", type=["xls", "xlsx", "csv"])

if file1 and file2:
    df_amd = pd.read_excel(file1) if file1.name.endswith(('xls', 'xlsx')) else pd.read_csv(file1)
    df2 = pd.read_excel(file2) if file2.name.endswith(('xls', 'xlsx')) else pd.read_csv(file2)

    st.subheader("AMD Main File Preview")
    st.dataframe(df_amd.head())

    st.subheader("Daily BP Alert File Preview")
    st.dataframe(df2.head())

    df_amd = df_amd[['BP Serial Number','Zone Subzone Type','Latest Transaction Date','BP Last Seen In_Vehicle_VIN','BP Last Seen In_Vehicle_Registration Number','BP Last Seen In_Vehicle _Vehicle Type','BP Last Seen In_Vehicle_Business Type','BP Last Seen In_Vehicle_Customer Name']]
    df_filtered = df_amd[df_amd['BP Serial Number'].isin(df2['BatterySerialNumber'])]

    st.subheader("✅ Processed Data")
    st.dataframe(df_filtered)

    csv = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        "⬇️ Download Processed CSV",
        data=csv,
        file_name="processed_data.csv",
        mime="text/csv"
    )

    

#%%
# df_amd = pd.read_csv("amd.csv")
# df_amd.info()
# #%%

# df_bp = pd.read_excel("bp_alert.xlsx", sheet_name="Export")
# df_bp = df_bp[['BatterySerialNumber']]


# df_1 = df_amd[['BP Serial Number','Zone Subzone Type','Latest Transaction Date','BP Last Seen In_Vehicle_VIN','BP Last Seen In_Vehicle_Registration Number','BP Last Seen In_Vehicle _Vehicle Type','BP Last Seen In_Vehicle_Business Type','BP Last Seen In_Vehicle_Customer Name']]
# df_filtered = df_1[df_1['BP Serial Number'].isin(df_bp['BatterySerialNumber'])]

