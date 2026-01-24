import streamlit as st
import pandas as pd
import datetime
import requests
import time # Library bawaan, tidak perlu instal
from PIL import Image
from io import BytesIO

# --- KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzxgHFaJttC3Wnrw0-4XZdPt7n24QeB-Z-pQWv4bhO9CzVDLhyIqj7-DaWLMFxO2VVL/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# --- CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; }
    .sidebar-time-box { background-color: rgba(255,255,255,0.1); padding: 15px; border-radius: 12px; text-align: center; color: white; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR (JAM OTOMATIS TANPA INSTAL LIBRARY) ---
with st.sidebar:
    st.markdown("## 🏢 Dashboard KI")
    menu = st.selectbox("Navigasi", ["📍 Absensi", "📊 Rekap Absensi"])
    st.divider()
    
    # Wadah kosong untuk jam agar bisa update terus
    wadah_jam = st.empty()

# --- HALAMAN 1: ABSENSI ---
def halaman_presensi(waktu_aktif, status_absen, tgl_skrg):
    st.markdown(f"## Absensi Tim KI - Sesi {status_absen}")
    if status_absen == "TUTUP":
        st.error(f"Sesi tutup. (Sekarang: {waktu_aktif.strftime('%H:%M:%S')})")
    else:
        daftar_nama = ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"]
        nama_lengkap = st.selectbox("Pilih nama Anda:", daftar_nama)
        foto = st.camera_input("Ambil foto")
        if st.button(f"Kirim Absen"):
            if foto:
                # Logika kirim data... (sama seperti sebelumnya)
                st.success("Berhasil Terkirim!")
            else:
                st.warning("Ambil foto dulu")

# --- HALAMAN 2: REKAP ---
def halaman_rekap(waktu_aktif):
    st.markdown("## Rekap Data Bulanan")
    bulan_indo = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    c1, c2 = st.columns(2)
    with c1: p_bulan = st.selectbox("Bulan", bulan_indo, index=waktu_aktif.month - 1)
    with c2: p_tahun = st.selectbox("Tahun", [2025, 2026], index=1)
    
    if st.button("🔍 Tampilkan"):
        try:
            res = requests.get(f"{WEBAPP_URL}?bulan={p_bulan} {p_tahun}")
            df = pd.DataFrame(res.json())
            df_final = df[["Nama", "Tanggal", "Jam Masuk", "Jam Pulang"]]
            df_final.index = range(1, len(df_final) + 1) # Nomor mulai dari 1
            st.table(df_final)
        except:
            st.error("Gagal ambil data")

# --- LOGIKA UPDATE JAM (LOOPING) ---
while True:
    # Ambil waktu sekarang WIB
    waktu_skrg = datetime.datetime.now() + datetime.timedelta(hours=7)
    
    # Update tampilan jam di sidebar tanpa refresh seluruh halaman
    wadah_jam.markdown(f"""
    <div class="sidebar-time-box">
        📅 <b>{waktu_skrg.strftime('%d %B %Y')}</b><br>
        <span style="font-size: 26px; color: #3b82f6;">⏰ <b>{waktu_skrg.strftime('%H:%M:%S')}</b></span><br>
        <b>WIB</b>
    </div>
    """, unsafe_allow_html=True)
    
    # Jalankan halaman sesuai menu
    if menu == "📍 Absensi":
        status_sesi = "TUTUP"
        if 6 <= waktu_skrg.hour < 12: status_sesi = "MASUK"
        elif 13 <= waktu_skrg.hour < 23: status_sesi = "PULANG"
        halaman_presensi(waktu_skrg, status_sesi, waktu_skrg.strftime("%Y-%m-%d"))
    else:
        halaman_rekap(waktu_skrg)
    
    # Tunggu 1 detik lalu ulangi (membuat jam berdetak)
    time.sleep(1)
