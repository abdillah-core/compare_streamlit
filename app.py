
import streamlit as st
import pandas as pd

st.title("Compare Rekening Koran vs Invoice - Versi Final dengan Export Excel")

# --- Upload File Rekening Koran ---
st.header("Upload Rekening Koran (Data 1)")
file1 = st.file_uploader("Upload Excel Rekening Koran", type=["xls", "xlsx"], key="file1")

# --- Upload File Invoice ---
st.header("Upload Invoice (Data 2)")
file2 = st.file_uploader("Upload Excel Invoice", type=["xls", "xlsx"], key="file2")

if file1 and file2:
    # --- Baca Data 1 ---
    df1 = pd.read_excel(file1)
    df1["Post Date"] = pd.to_datetime(df1["Post Date"], dayfirst=True, errors='coerce')
    df1 = df1.dropna(subset=["Post Date", "Amount"])
    df1["Tanggal"] = df1["Post Date"].dt.date

    # --- Baca Data 2 ---
    df2 = pd.read_excel(file2)
    df2["TANGGAL INVOICE"] = pd.to_datetime(df2["TANGGAL INVOICE"], errors='coerce')
    df2 = df2.dropna(subset=["TANGGAL INVOICE", "HARGA"])
    df2["Tanggal"] = df2["TANGGAL INVOICE"].dt.date

    # --- Jumlahkan HARGA per tanggal ---
    df2_grouped = df2.groupby("Tanggal")["HARGA"].sum().reset_index()

    # --- Gabungkan jumlah invoice ke df1 sesuai tanggal ---
    df1 = df1.merge(df2_grouped, on="Tanggal", how="left")
    df1["HARGA"] = df1["HARGA"].fillna(0)

    # --- Hitung selisih per baris ---
    df1["Selisih"] = df1["Amount"] - df1["HARGA"]

    # --- Siapkan DataFrame hasil sesuai kolom yang diminta ---
    output_df = df1[[
        "Post Date", "Branch", "Journal No.", "Description", "Amount"
    ]].copy()

    output_df["Invoice"] = df1["HARGA"]
    output_df["Selisih"] = df1["Selisih"]
    output_df["Db/Cr"] = df1["Db/Cr"]
    output_df["Balance"] = df1["Balance"]

    st.header("Hasil Compare Detail")
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
