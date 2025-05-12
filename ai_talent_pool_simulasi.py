
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="AI Talent Pool Dashboard", layout="wide")

st.title("📊 AI Talent Pool Classification & Simulation")
st.markdown("Aplikasi berbasis AI untuk klasifikasi dan analisis kinerja pekerja berdasarkan KPI")

# ==================== 1. Upload Excel Dinamis ====================
uploaded_file = st.file_uploader("📤 Upload file KPI (CSV/XLSX)", type=["csv", "xlsx"])

if uploaded_file:
    if uploaded_file.name.endswith("csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
else:
    st.stop()

# ==================== 2. Data Preprocessing ====================
df['REALISASI TW TERKAIT'] = pd.to_numeric(df['REALISASI TW TERKAIT'], errors='coerce')
df['TARGET TW TERKAIT'] = pd.to_numeric(df['TARGET TW TERKAIT'], errors='coerce')
df['BOBOT'] = pd.to_numeric(df['BOBOT'], errors='coerce')
df['POLARITAS'] = df['POLARITAS'].str.strip().str.lower()

def calculate_capaian(row):
    realisasi = row['REALISASI TW TERKAIT']
    target = row['TARGET TW TERKAIT']
    polaritas = row['POLARITAS']
    if pd.isna(realisasi) or pd.isna(target) or target == 0 or realisasi == 0:
        return None
    if polaritas == 'positif':
        return (realisasi / target) * 100
    elif polaritas == 'negatif':
        return (target / realisasi) * 100
    else:
        return None

df['CAPAIAN (%)'] = df.apply(calculate_capaian, axis=1)
df['SKOR KPI'] = df['CAPAIAN (%)'] * df['BOBOT'] / 100

summary = df.groupby(['NIPP PEKERJA', 'POSISI PEKERJA', 'PERUSAHAAN'], as_index=False).agg(
    TOTAL_SKOR=('SKOR KPI', 'sum'),
    TOTAL_BOBOT=('BOBOT', 'sum')
)
summary = summary[summary['TOTAL_BOBOT'] != 0]
summary['SKOR AKHIR'] = (summary['TOTAL_SKOR'] / summary['TOTAL_BOBOT']) * 100

def classify_performance(score):
    if score > 110:
        return "Istimewa"
    elif score > 105:
        return "Sangat Baik"
    elif score >= 90:
        return "Baik"
    elif score >= 80:
        return "Cukup"
    else:
        return "Kurang"

summary['KATEGORI TALENT'] = summary['SKOR AKHIR'].apply(classify_performance)

# ==================== 3. Simulasi Kalibrasi Kuota ====================
st.sidebar.header("⚙️ Simulasi Kalibrasi Kuota")
kuota_istimewa = st.sidebar.slider("Kuota Istimewa (%)", 0, 100, 10)
kuota_sangat_baik = st.sidebar.slider("Kuota Sangat Baik (%)", 0, 100, 15)
kuota_baik = st.sidebar.slider("Kuota Baik (%)", 0, 100, 50)
kuota_cukup = st.sidebar.slider("Kuota Cukup (%)", 0, 100, 15)
kuota_kurang = st.sidebar.slider("Kuota Kurang (%)", 0, 100, 10)

total_kuota = kuota_istimewa + kuota_sangat_baik + kuota_baik + kuota_cukup + kuota_kurang
if total_kuota != 100:
    st.sidebar.warning("⚠️ Total kuota harus 100%")

# ==================== 4. Visualisasi Talent ====================
st.subheader("📌 Tabel Talent Pool")
st.dataframe(summary)

st.subheader("📊 Distribusi Talent Pool (As Is)")
fig_pie = px.pie(summary, names='KATEGORI TALENT', title='Distribusi Kategori Talent (Sebelum Simulasi)')
st.plotly_chart(fig_pie)

# ==================== 5. Visualisasi Time Series per Jabatan ====================
st.subheader("📈 Tren Skor KPI Akhir per Jabatan")
if 'PERIODE' in df.columns:
    time_summary = df.copy()
    time_summary['PERIODE'] = time_summary['PERIODE'].astype(str)
    trend = time_summary.groupby(['POSISI PEKERJA', 'PERIODE'], as_index=False).agg(Skor_Akhir=('SKOR KPI', 'mean'))
    posisi = st.selectbox("Pilih Posisi", trend['POSISI PEKERJA'].unique())
    fig_line = px.line(trend[trend['POSISI PEKERJA'] == posisi], x='PERIODE', y='Skor_Akhir', markers=True, title=f"Skor Rata-rata KPI untuk {posisi}")
    st.plotly_chart(fig_line)
else:
    st.info("Tambahkan kolom 'PERIODE' di data untuk visualisasi time-series per jabatan.")
