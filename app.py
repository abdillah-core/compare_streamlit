
import streamlit as st
import pandas as pd
import re
from datetime import timedelta

st.title("Compare Rekening Koran vs Invoice - Output 10 Kolom Final")

# --- Input Periode Rekonsiliasi ---
st.header("Periode Rekonsiliasi")
start_date = st.date_input("Tanggal Mulai")
end_date = st.date_input("Tanggal Selesai")

# --- Upload File Rekening Koran ---
st.header("Upload Rekening Koran (Data 1)")
file1 = st.file_uploader("Upload Excel Rekening Koran", type=["xls", "xlsx"], key="file1")

# --- Upload File Invoice ---
st.header("Upload Invoice (Data 2)")
file2 = st.file_uploader("Upload Excel Invoice", type=["xls", "xlsx"], key="file2")

if file1 and file2 and start_date and end_date:
    tanggal_list = pd.date_range(start=start_date, end=end_date)
    df_output = pd.DataFrame({"Tanggal": tanggal_list.strftime("%d %b %Y").str.upper()})

    df1 = pd.read_excel(file1)
    df1["Post Date"] = pd.to_datetime(df1["Post Date"], dayfirst=True, errors='coerce')
    df1 = df1.dropna(subset=["Post Date", "Amount"])

    df1 = df1[(df1["Branch"].str.contains("UNIT E-CHANNEL", na=False)) & (df1["Amount"] > 100_000_000)].copy()

    def extract_trx_date(text):
        if pd.isnull(text):
            return None
        match = re.search(r'TRX TGL ([0-9]{2} [A-Z]{3})', text)
        year_match = re.search(r'([0-9]{4})', text)
        if match and year_match:
            return f"{match.group(1)} {year_match.group(1)}"
        return None

    df1["Tanggal TRX"] = df1["Description"].apply(extract_trx_date)

    df2 = pd.read_excel(file2)
    df2["TANGGAL INVOICE"] = pd.to_datetime(df2["TANGGAL INVOICE"], errors='coerce')
    df2 = df2.dropna(subset=["TANGGAL INVOICE", "HARGA"])

    df2["Tanggal"] = df2["TANGGAL INVOICE"].dt.strftime("%d %b %Y").str.upper()
    df2_grouped = df2.groupby("Tanggal")["HARGA"].sum().reset_index()

    # Siapkan kolom output kosong
    df_output["Post Date"] = None
    df_output["Branch"] = None
    df_output["Journal No."] = None
    df_output["Description"] = None
    df_output["Amount"] = 0
    df_output["Invoice"] = 0
    df_output["Selisih"] = 0
    df_output["Db/Cr"] = None
    df_output["Balance"] = None

    # Isi data dari Data 1
    for idx, row in df_output.iterrows():
        tanggal_row = row["Tanggal"]
        df1_match = df1[df1["Tanggal TRX"] == tanggal_row]

        if not df1_match.empty:
            first_match = df1_match.iloc[0]
            df_output.at[idx, "Post Date"] = first_match["Post Date"]
            df_output.at[idx, "Branch"] = first_match["Branch"]
            df_output.at[idx, "Journal No."] = first_match["Journal No."]
            df_output.at[idx, "Description"] = first_match["Description"]
            df_output.at[idx, "Amount"] = first_match["Amount"]
            df_output.at[idx, "Db/Cr"] = first_match["Db/Cr"]
            df_output.at[idx, "Balance"] = first_match["Balance"]

    # Merge Invoice dari Data 2 TANPA MENGHILANGKAN BARIS
    df_output = pd.merge(df_output, df2_grouped, on="Tanggal", how="left")
    df_output["Invoice"] = df_output["HARGA"].fillna(0)
    df_output.drop(columns=["HARGA"], inplace=True)

    # Hitung Selisih
    df_output["Selisih"] = df_output["Amount"] - df_output["Invoice"]

    st.write("Jumlah baris final:", len(df_output))

    st.header("Hasil Compare Detail (10 Kolom)")
    st.dataframe(df_output.fillna(""))

    import io
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_output.to_excel(writer, index=False, sheet_name='Compare Hasil')
    output.seek(0)

    st.download_button(
        label="Download Hasil Compare (Excel)",
        data=output,
        file_name="hasil_compare.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Silakan upload kedua file dan pilih periode untuk melanjutkan.")
