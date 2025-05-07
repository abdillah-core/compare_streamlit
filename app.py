
import streamlit as st
import pandas as pd
import re

st.title("Compare Rekening Koran vs Invoice - Versi Final dengan Output 10 Kolom")

# --- Input Periode Rekonsiliasi ---
st.header("Periode Rekonsiliasi")
start_date = st.date_input("Tanggal Mulai")
end_date = st.date_input("Tanggal Selesai")

# --- Upload File Rekening Koran (Data 1) ---
st.header("Upload Rekening Koran (Data 1)")
file1 = st.file_uploader("Upload Excel Rekening Koran", type=["xls", "xlsx"], key="file1")

# --- Upload File Invoice (Data 2) ---
st.header("Upload Invoice (Data 2)")
file2 = st.file_uploader("Upload Excel Invoice", type=["xls", "xlsx"], key="file2")

if file1 and file2 and start_date and end_date:
    df1 = pd.read_excel(file1)
    df1["Post Date"] = pd.to_datetime(df1["Post Date"], dayfirst=True, errors='coerce')
    df1 = df1.dropna(subset=["Post Date", "Amount"])

    df1_filtered = df1[(df1["Branch"].str.contains("UNIT E-CHANNEL", na=False)) & (df1["Amount"] > 100_000_000)].copy()

    def extract_start_trx_date(text):
        if pd.isnull(text):
            return None
        match = re.search(r'TRX TGL ([0-9]{2} [A-Z]{3})(?:-[0-9]{2} [A-Z]{3})? ([0-9]{4})', text)
        if match:
            return f"{match.group(1)} {match.group(2)}"
        return None

    df1_filtered["Tanggal"] = df1_filtered["Description"].apply(extract_start_trx_date)

    def trx_date_in_range(trx_date):
        try:
            trx_datetime = pd.to_datetime(trx_date, format="%d %b %Y", errors='coerce')
            return pd.notnull(trx_datetime) and start_date <= trx_datetime.date() <= end_date
        except:
            return False

    df1_filtered = df1_filtered[df1_filtered["Tanggal"].apply(trx_date_in_range)].copy()

    df2 = pd.read_excel(file2)
    df2["TANGGAL INVOICE"] = pd.to_datetime(df2["TANGGAL INVOICE"], errors='coerce')
    df2 = df2.dropna(subset=["TANGGAL INVOICE", "HARGA"])

    df2 = df2[(df2["TANGGAL INVOICE"].dt.date >= start_date) & (df2["TANGGAL INVOICE"].dt.date <= end_date)]

    df2["Tanggal"] = df2["TANGGAL INVOICE"].dt.strftime("%d %b %Y").str.upper()

    df2_grouped = df2.groupby("Tanggal")["HARGA"].sum().reset_index()

    df1_filtered = df1_filtered.merge(df2_grouped, left_on="Tanggal", right_on="Tanggal", how="left")
    df1_filtered["HARGA"] = df1_filtered["HARGA"].fillna(0)

    df1_filtered["Selisih"] = df1_filtered["Amount"] - df1_filtered["HARGA"]

    output_df = pd.DataFrame()
    output_df["Tanggal"] = df1_filtered["Tanggal"]
    output_df["Post Date"] = df1_filtered["Post Date"]
    output_df["Branch"] = df1_filtered["Branch"]
    output_df["Journal No."] = df1_filtered["Journal No."]
    output_df["Description"] = df1_filtered["Description"]
    output_df["Amount"] = df1_filtered["Amount"]
    output_df["Invoice"] = df1_filtered["HARGA"]
    output_df["Selisih"] = df1_filtered["Selisih"]
    output_df["Db/Cr"] = df1_filtered["Db/Cr"]
    output_df["Balance"] = df1_filtered["Balance"]

    st.header("Hasil Compare Detail (10 Kolom)")
    st.dataframe(output_df)

    import io
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        output_df.to_excel(writer, index=False, sheet_name='Compare Hasil')
    output.seek(0)

    st.download_button(
        label="Download Hasil Compare (Excel)",
        data=output,
        file_name="hasil_compare.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Silakan upload kedua file dan pilih periode untuk melanjutkan.")
