import streamlit as st
import pandas as pd

st.title("Compare Rekening Koran vs Invoice - Versi Final dengan Output 10 Kolom")

# --- Upload File Rekening Koran (Data 1) ---
st.header("Upload Rekening Koran (Data 1)")
file1 = st.file_uploader("Upload Excel Rekening Koran", type=["xls", "xlsx"], key="file1")

# --- Upload File Invoice (Data 2) ---
st.header("Upload Invoice (Data 2)")
file2 = st.file_uploader("Upload Excel Invoice", type=["xls", "xlsx"], key="file2")

if file1 and file2:
    # --- Baca Data 1 ---
    df1 = pd.read_excel(file1)
    df1["Post Date"] = pd.to_datetime(df1["Post Date"], dayfirst=True, errors='coerce')
    df1 = df1.dropna(subset=["Post Date", "Amount"])
    df1["Tanggal"] = df1["Post Date"].dt.date

    # Filter hanya baris dengan Branch = UNIT E-CHANNEL dan Amount > 100 juta
    df1_filtered = df1[(df1["Branch"].str.contains("UNIT E-CHANNEL", na=False)) & (df1["Amount"] > 100_000_000)].copy()

    # --- Baca Data 2 ---
    df2 = pd.read_excel(file2)
    df2["TANGGAL INVOICE"] = pd.to_datetime(df2["TANGGAL INVOICE"], errors='coerce')
    df2 = df2.dropna(subset=["TANGGAL INVOICE", "HARGA"])
    df2["Tanggal"] = df2["TANGGAL INVOICE"].dt.date

    # --- Jumlahkan HARGA per tanggal ---
    df2_grouped = df2.groupby("Tanggal")["HARGA"].sum().reset_index()

    # --- Gabungkan jumlah invoice ke df1_filtered sesuai tanggal ---
    df1_filtered = df1_filtered.merge(df2_grouped, on="Tanggal", how="left")
    df1_filtered["HARGA"] = df1_filtered["HARGA"].fillna(0)

    # --- Hitung selisih per baris ---
    df1_filtered["Selisih"] = df1_filtered["Amount"] - df1_filtered["HARGA"]

    # --- Siapkan DataFrame hasil sesuai revisi 10 kolom ---
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

    # --- Download hasil ke Excel ---
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
    st.info("Silakan upload kedua file untuk melanjutkan.")
