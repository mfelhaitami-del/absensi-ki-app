import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image, ImageOps
from io import BytesIO

# --- KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbyHMhEr0zy226CjIzHEGQJL0PUsMO3AI6EtZGUOTtDEX6DSqOKaRRrG1EE-eyVxXZES/exec"

st.set_page_config(page_title="Absensi KI", layout="wide")

# Waktu Sekarang
waktu_now = datetime.datetime.now() + datetime.timedelta(hours=7)
bulan_indo = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]

menu = st.sidebar.selectbox("Pilih Menu", ["📍 Presensi", "📊 Rekap Absensi"])

if menu == "📍 Presensi":
    st.title("📸 Absensi Foto Real-Time")
    # (Kode presensi tetap sama seperti sebelumnya...)
    # ... bagian presensi Anda ...
    st.info(f"Sesi Aktif: {waktu_now.strftime('%d %B %Y')}")
    # [Tambahkan kode presensi Anda di sini]

elif menu == "📊 Rekap Absensi":
    st.title("📊 Rekap Absensi Tim KI")
    
    # --- FITUR PILIH BULAN ---
    col1, col2 = st.columns([2, 1])
    with col1:
        pilih_bulan = st.selectbox("Pilih Bulan", bulan_indo, index=waktu_now.month - 1)
    with col2:
        pilih_tahun = st.selectbox("Pilih Tahun", [2025, 2026, 2027], index=1)
    
    nama_tab_target = f"{pilih_bulan} {pilih_tahun}"
    
    if st.button("🔍 Tampilkan Data"):
        st.cache_data.clear()
        try:
            # Mengirim parameter bulan ke Apps Script
            res = requests.get(f"{WEBAPP_URL}?bulan={nama_tab_target}")
            data_json = res.json()
            
            if data_json:
                df = pd.DataFrame(data_json)
                df.columns = ["Nama", "Tanggal", "Jam Masuk", "Jam Pulang", "Link Foto"]
                st.write(f"### Data Absensi: {nama_tab_target}")
                st.dataframe(df, use_container_width=True)
                
                # Fitur Download
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download CSV", csv, f"Rekap_{nama_tab_target}.csv", "text/csv")
            else:
                st.warning(f"Tidak ada data ditemukan untuk tab: {nama_tab_target}")
        except Exception as e:
            st.error(f"Gagal memuat data: {e}")
