import streamlit as st
import pandas as pd
import datetime
import requests

# --- KONFIGURASI ---
# Pastikan URL di bawah ini diapit tanda petik dengan benar
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxjdyJJTa4gwdFcSzqfVRiHF_jx2Xr7CF4N7HgxzsWZY_9mnww2BxuGYKmj_lYNMpSv/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
    .hero-title { font-size: 40px; font-weight: 800; color: #ffffff; text-align: center; }
    </style>
""", unsafe_allow_html=True)

def halaman_rekap():
    st.markdown('<p class="hero-title">Rekap Data Bulanan</p>', unsafe_allow_html=True)
    
    bulan_indo = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    waktu_skrg = datetime.datetime.now() + datetime.timedelta(hours=7)
    
    c1, c2 = st.columns(2)
    with c1: p_bulan = st.selectbox("Pilih Bulan", bulan_indo, index=waktu_skrg.month - 1)
    with c2: p_tahun = st.selectbox("Pilih Tahun", [2025, 2026], index=1)
    
    if st.button("🔍 Tampilkan Data Laporan"):
        st.cache_data.clear()
        nama_tab = f"{p_bulan} {p_tahun}"
        try:
            res = requests.get(f"{WEBAPP_URL}?bulan={nama_tab}")
            data_json = res.json()
            
            if data_json:
                # Membaca data sebagai teks murni
                df = pd.DataFrame(data_json)
                
                # Memilih kolom yang ingin ditampilkan saja
                kolom_target = ["Nama", "Tanggal", "Jam Masuk", "Jam Pulang"]
                df_display = df[[c for c in kolom_target if c in df.columns]]
                
                st.success(f"Menampilkan data untuk {nama_tab}")
                # Menggunakan st.table agar format teks jam tidak berubah
                st.table(df_display)
            else:
                st.info(f"Tidak ada data di sheet '{nama_tab}'")
        except Exception as e:
            st.error(f"Error: {e}")

halaman_rekap()
