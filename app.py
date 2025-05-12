import streamlit as st
import pandas as pd

# Load data
@st.cache_data
def load_data():
    return pd.read_csv("kpi_cleaned.csv")

df = load_data()

# Preprocessing
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

# Aggregation per individual
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

# UI Streamlit
st.title("AI Talent Pool Classification")
st.markdown("🔍 Klasifikasi pekerja berdasarkan skor akhir KPI dan kategori talent pool")

filter_perusahaan = st.selectbox("🏢 Filter berdasarkan Perusahaan", options=["Semua"] + list(summary['PERUSAHAAN'].unique()))
if filter_perusahaan != "Semua":
    filtered = summary[summary['PERUSAHAAN'] == filter_perusahaan]
else:
    filtered = summary

st.dataframe(filtered)

# Download Excel
st.download_button("📥 Download Talent Classification (Excel)", data=filtered.to_csv(index=False), file_name="talent_classification.csv", mime="text/csv")
