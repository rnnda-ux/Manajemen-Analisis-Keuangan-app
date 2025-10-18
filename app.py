import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

# ==============================
# KONFIGURASI DASHBOARD
# ==============================
st.set_page_config(page_title="💼 Sistem Manajemen & Analisis Keuangan", layout="wide")

st.title("💼 Sistem Manajemen & Analisis Keuangan")
st.markdown("Sistem ini membantu mencatat, menganalisis, dan mengelola keuangan perusahaan secara interaktif dan real-time.")

# ==============================
# FILE DATA
# ==============================
DATA_FILE = "data_keuangan.csv"

def load_data():
    try:
        df = pd.read_csv(DATA_FILE)
        df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce", format="mixed")
        df = df.dropna(subset=["Tanggal"])
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=["Tanggal", "Keterangan", "Kategori", "Jumlah"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# ==============================
# SIDEBAR NAVIGASI
# ==============================
menu = st.sidebar.radio("📌 Menu Utama", [
    "📥 Input Transaksi",
    "📊 Analisis Keuangan",
    "⚙️ Kelola Data"
])

# ==============================
# MENU 1: INPUT TRANSAKSI
# ==============================
if menu == "📥 Input Transaksi":
    st.header("📝 Input Data Transaksi Keuangan")

    with st.form("form_transaksi"):
        tanggal = st.date_input("Tanggal", datetime.now().date())
        keterangan = st.text_input("Keterangan Transaksi")
        kategori = st.selectbox("Kategori", ["Pendapatan", "Pengeluaran"])
        jumlah = st.number_input("Jumlah (Rp)", min_value=0, step=1000)
        submitted = st.form_submit_button("💾 Simpan Transaksi")

        if submitted:
            if keterangan and jumlah > 0:
                new_data = pd.DataFrame([{
                    "Tanggal": tanggal.strftime("%Y-%m-%d"),
                    "Keterangan": keterangan,
                    "Kategori": kategori,
                    "Jumlah": jumlah
                }])
                df = load_data()
                df = pd.concat([df, new_data], ignore_index=True)
                save_data(df)
                st.success("✅ Transaksi berhasil disimpan!")
            else:
                st.error("⚠️ Harap isi semua kolom dengan benar.")

    st.markdown("### 📋 Riwayat Transaksi Terakhir")
    df = load_data()
    st.dataframe(df.sort_values("Tanggal", ascending=False).head(10), use_container_width=True)

# ==============================
# MENU 2: ANALISIS KEUANGAN
# ==============================
elif menu == "📊 Analisis Keuangan":
    st.header("📈 Analisis Data Keuangan")
    df = load_data()

    if df.empty:
        st.warning("Belum ada data transaksi. Tambahkan data terlebih dahulu di menu **Input Transaksi**.")
        st.stop()

    # ==============================
    # FILTER WAKTU + KATEGORI
    # ==============================
    st.subheader("🗓️ Filter Analisis")

    col1, col2, col3 = st.columns(3)
    with col1:
        tahun_tersedia = sorted(df["Tanggal"].dt.year.unique(), reverse=True)
        tahun_pilih = st.selectbox("Tahun", tahun_tersedia, index=0)

    with col2:
        bulan_tersedia = sorted(df[df["Tanggal"].dt.year == tahun_pilih]["Tanggal"].dt.month.unique())
        bulan_pilih = st.selectbox("Bulan", ["Semua Bulan"] + [str(b) for b in bulan_tersedia])

    with col3:
        kategori_pilih = st.selectbox("Kategori", ["Semua", "Pendapatan", "Pengeluaran"])

    df_tampil = df[df["Tanggal"].dt.year == tahun_pilih]
    if bulan_pilih != "Semua Bulan":
        df_tampil = df_tampil[df_tampil["Tanggal"].dt.month == int(bulan_pilih)]
    if kategori_pilih != "Semua":
        df_tampil = df_tampil[df_tampil["Kategori"] == kategori_pilih]

    if df_tampil.empty:
        st.warning("Tidak ada transaksi sesuai filter yang dipilih.")
        st.stop()

    # ==============================
    # LAPORAN LABA RUGI
    # ==============================
    st.subheader("💰 Laporan Laba Rugi")

    total_pendapatan = df_tampil[df_tampil["Kategori"] == "Pendapatan"]["Jumlah"].sum()
    total_pengeluaran = df_tampil[df_tampil["Kategori"] == "Pengeluaran"]["Jumlah"].sum()
    laba_bersih = total_pendapatan - total_pengeluaran

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Pendapatan", f"Rp {total_pendapatan:,.0f}")
    col2.metric("Total Pengeluaran", f"Rp {total_pengeluaran:,.0f}")
    col3.metric("Laba Bersih", f"Rp {laba_bersih:,.0f}")

    st.markdown("---")

    # ==============================
    # ANALISIS RASIO KEUANGAN
    # ==============================
    st.subheader("📊 Analisis Rasio Keuangan")

    total_aset = st.number_input("Total Aset (Rp)", min_value=0, value=50000000, step=1000000)
    total_kewajiban = st.number_input("Total Kewajiban (Rp)", min_value=0, value=20000000, step=1000000)
    modal_sendiri = total_aset - total_kewajiban

    ROA = (laba_bersih / total_aset) * 100 if total_aset else 0
    ROE = (laba_bersih / modal_sendiri) * 100 if modal_sendiri else 0
    Current_Ratio = (total_aset / total_kewajiban) if total_kewajiban else 0
    Quick_Ratio = ((total_aset * 0.8) / total_kewajiban) if total_kewajiban else 0

    colA, colB, colC, colD = st.columns(4)
    colA.metric("ROA (Return on Assets)", f"{ROA:.2f}%")
    colB.metric("ROE (Return on Equity)", f"{ROE:.2f}%")
    colC.metric("Current Ratio", f"{Current_Ratio:.2f}x")
    colD.metric("Quick Ratio", f"{Quick_Ratio:.2f}x")

    # ==============================
    # TREN KEUANGAN
    # ==============================
    st.subheader("📉 Tren Keuangan Bulanan")

    df_tampil["Bulan"] = df_tampil["Tanggal"].dt.to_period("M")
    monthly = df_tampil.groupby(["Bulan", "Kategori"])["Jumlah"].sum().unstack(fill_value=0)
    monthly["Laba Bersih"] = monthly.get("Pendapatan", 0) - monthly.get("Pengeluaran", 0)

    kolom_chart = [col for col in ["Pendapatan", "Pengeluaran", "Laba Bersih"] if col in monthly.columns]
    if kolom_chart:
        st.line_chart(monthly[kolom_chart])
    else:
        st.info("📊 Tidak ada data untuk ditampilkan dalam grafik.")

    # ==============================
    # INTERPRETASI OTOMATIS
    # ==============================
    st.subheader("🧠 Interpretasi Otomatis")

    interpretasi = []
    if laba_bersih > 0:
        interpretasi.append("✅ Kondisi keuangan **menguntungkan (profit)**.")
    else:
        interpretasi.append("⚠️ Perusahaan mengalami **kerugian**, perlu pengendalian biaya.")

    if ROA < 5:
        interpretasi.append("📉 **ROA rendah**, efisiensi aset perlu ditingkatkan.")
    else:
        interpretasi.append("💹 **ROA baik**, aset menghasilkan laba optimal.")

    if Current_Ratio < 1:
        interpretasi.append("⚠️ **Likuiditas rendah**, kewajiban jangka pendek sulit dipenuhi.")
    else:
        interpretasi.append("💧 **Likuiditas sehat**, aset lancar cukup untuk menutup kewajiban.")

    for i in interpretasi:
        st.markdown(f"- {i}")

    # ==============================
    # EKSPOR PDF
    # ==============================
    st.markdown("---")
    st.subheader("📄 Ekspor Laporan ke PDF")

    if st.button("🧾 Buat Laporan PDF"):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("💼 LAPORAN ANALISIS KEUANGAN", styles["Title"]))
        elements.append(Paragraph(f"Tanggal Analisis: {datetime.now().strftime('%d %B %Y')}", styles["Normal"]))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("<b>Laba Rugi</b>", styles["Heading2"]))
        data_lr = [
            ["Pendapatan", f"Rp {total_pendapatan:,.0f}"],
            ["Pengeluaran", f"Rp {total_pengeluaran:,.0f}"],
            ["Laba Bersih", f"Rp {laba_bersih:,.0f}"]
        ]
        t = Table(data_lr, colWidths=[150, 200])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        elements.append(t)
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("<b>Rasio Keuangan</b>", styles["Heading2"]))
        data_rs = [
            ["ROA", f"{ROA:.2f}%"],
            ["ROE", f"{ROE:.2f}%"],
            ["Current Ratio", f"{Current_Ratio:.2f}x"],
            ["Quick Ratio", f"{Quick_Ratio:.2f}x"]
        ]
        t2 = Table(data_rs, colWidths=[150, 200])
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        elements.append(t2)
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("<b>Interpretasi Otomatis</b>", styles["Heading2"]))
        for i in interpretasi:
            elements.append(Paragraph(f"- {i}", styles["Normal"]))

        doc.build(elements)

        st.download_button(
            label="📥 Download Laporan PDF",
            data=buffer.getvalue(),
            file_name="laporan_keuangan.pdf",
            mime="application/pdf"
        )

# ==============================
# MENU 3: KELOLA DATA
# ==============================
elif menu == "⚙️ Kelola Data":
    st.header("⚙️ Kelola Data Keuangan")
    df = load_data()

    if df.empty:
        st.warning("Belum ada data transaksi yang tersimpan.")
        st.stop()

    # Download CSV
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False)
    st.download_button("📥 Download Data CSV", buffer.getvalue(), file_name="data_keuangan.csv", mime="text/csv")

    # Upload CSV
    st.subheader("📤 Upload File CSV Baru")
    uploaded = st.file_uploader("Unggah file data_keuangan.csv", type="csv")
    if uploaded:
        new_df = pd.read_csv(uploaded)
        save_data(new_df)
        st.success("✅ File berhasil diunggah dan disimpan!")

    # Hapus data tertentu
    st.subheader("🗑️ Hapus Transaksi Tertentu")
    df = df.reset_index().rename(columns={"index": "ID"})
    selected_id = st.selectbox("Pilih ID transaksi yang akan dihapus:", df["ID"])
    st.write(df.loc[selected_id])

    if st.button("❌ Hapus Transaksi Ini"):
        df = df.drop(selected_id)
        df = df.drop(columns=["ID"])
        save_data(df)
        st.success("✅ Transaksi berhasil dihapus!")

    if st.button("⚠️ Hapus Semua Data"):
        save_data(pd.DataFrame(columns=["Tanggal", "Keterangan", "Kategori", "Jumlah"]))
        st.warning("🚨 Semua data telah dihapus!")
