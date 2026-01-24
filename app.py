import streamlit as st
import pandas as pd
import datetime
import requests

# --- KONFIGURASI ---
WEBAPP_URL = "import streamlit as st
import pandas as pd
import datetime
import requests

# --- KONFIGURASI ---
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxrIdq6kURT3jozVuXT6AIuAzOeCo2vzlO4woWpNUg6JJ7z3zHymMMDx4vbw8QP6pPu/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# --- HALAMAN REKAP ---
def halaman_rekap():
    st.markdown("### 📋 Rekap Data Bulanan")
    
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
                # Mengambil data murni tanpa konversi Pandas
                df = pd.DataFrame(data_json)
                
                # Memastikan kolom yang diambil hanya yang diperlukan
                kolom_tersedia = df.columns.tolist()
                kolom_tampil = ["Nama", "Tanggal", "Jam Masuk", "Jam Pulang"]
                
                # Filter hanya kolom yang ada di sheet
                df_final = df[[c for c in kolom_tampil if c in kolom_tersedia]]
                
                st.write(f"**Laporan: {nama_tab}**")
                # Menggunakan st.table agar teks jam tidak diubah-ubah oleh browser
                st.table(df_final)
            else:
                st.info("ℹ️ Tidak ada data untuk bulan ini.")
        except:
            st.error("❌ Gagal mengambil data. Pastikan URL Apps Script benar.")

# --- MAIN ---
halaman_rekap()"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# --- HALAMAN REKAP ---
def halaman_rekap():
    st.markdown("### 📋 Rekap Data Bulanan")
    
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
                # Mengambil data murni tanpa konversi Pandas
                df = pd.DataFrame(data_json)
                
                # Memastikan kolom yang diambil hanya yang diperlukan
                kolom_tersedia = df.columns.tolist()
                kolom_tampil = ["Nama", "Tanggal", "Jam Masuk", "Jam Pulang"]
                
                # Filter hanya kolom yang ada di sheet
                df_final = df[[c for c in kolom_tampil if c in kolom_tersedia]]
                
                st.write(f"**Laporan: {nama_tab}**")
                # Menggunakan st.table agar teks jam tidak diubah-ubah oleh browser
                st.table(df_final)
            else:
                st.info("ℹ️ Tidak ada data untuk bulan ini.")
        except:
            st.error("❌ Gagal mengambil data. Pastikan URL Apps Script benar.")

# --- MAIN ---
halaman_rekap()
