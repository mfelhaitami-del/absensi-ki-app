import streamlit as st
import pandas as pd
import datetime
import requests
import time
from PIL import Image
from io import BytesIO

# --- KONFIGURASI ---
# GANTI URL DI BAWAH INI (Pastikan diapit dua tanda kutip "")
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzxgHFaJttC3Wnrw0-4XZdPt7n24QeB-Z-pQWv4bhO9CzVDLhyIqj7-DaWLMFxO2VVL/exec"

st.set_page_config(page_title="Absensi Tim KI Satker PPS Banten", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    .hero-title { font-size: 50px; font-weight: 800; color: #ffffff !important; text-align: center; }
    .sidebar-time-box { background-color: rgba(255,255,255,0.1); padding: 12px; border-radius: 10px; margin-top: 10px; border: 1px solid rgba(255,255,255,0.2); }
    </style>
""", unsafe_allow_html=True)

# --- HALAMAN 1: PRESENSI ---
def halaman_presensi(waktu_aktif, status_absen, tgl_skrg):
    st.markdown('<p class="hero-title">Absensi Tim KI Satker PPS Banten</p>', unsafe_allow_html=True)
    if status_absen == "TUTUP":
        st.error(f"🚫 Sesi tutup. (Sekarang: {waktu_aktif.strftime('%H:%M:%S')} WIB)")
    else:
        daftar_nama = ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"]
        nama_lengkap = st.selectbox("Pilih nama Anda:", daftar_nama)
        st.info(f"📍 Sesi: **Absen {status_absen}**")
        foto = st.camera_input("Ambil foto wajah")

        if st.button(f"Kirim Absensi {status_absen}"):
            if foto:
                try:
                    img = Image.open(foto)
                    buf = BytesIO()
                    img.save(buf, format="JPEG")
                    files = {"image": buf.getvalue()}
                    resp = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files=files)
                    link_foto = resp.json()["data"]["url"]
                    
                    jam_fix = waktu_aktif.strftime("%H:%M:%S")
                    payload = {"nama": nama_lengkap, "tanggal": tgl_skrg, "jam": jam_fix, "status": status_absen, "foto_link": link_foto}
                    requests.post(WEBAPP_URL, json=payload)
                    st.success(f"Berhasil! Tercatat jam {jam_fix} WIB.")
                except:
                    st.error("Gagal mengirim.")
            else:
                st.warning("⚠️ Ambil foto dulu!")

# --- HALAMAN 2: REKAP ---
def halaman_rekap(waktu_aktif):
    st.markdown('<p class="hero-title" style="font-size:40px;">Rekap Data Bulanan</p>', unsafe_allow_html=True)
    bulan_indo = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    
    c1, c2 = st.columns(2)
    with c1: p_bulan = st.selectbox("Pilih Bulan", bulan_indo, index=waktu_aktif.month - 1)
    with c2: p_tahun = st.selectbox("Pilih Tahun", [2025, 2026], index=1)
    
    if st.button("🔍 Tampilkan Data Laporan"):
        st.cache_data.clear()
        nama_tab = f"{p_bulan} {p_tahun}"
        try:
            res = requests.get(f"{WEBAPP_URL}?bulan={nama_tab}")
            data_json = res.json()
            if data_json:
                df = pd.DataFrame(data_json)
                # Tampilkan Nama, Tanggal, Jam Masuk, Jam Pulang
                df_display = df[["Nama", "Tanggal", "Jam Masuk", "Jam Pulang"]]
                st.write(f"### 📋 Laporan: {nama_tab}")
                st.table(df_display) # Jam akan identik dengan Sheet karena getDisplayValues
            else:
                st.info("Data tidak ditemukan.")
        except:
            st.error("Gagal memuat data. Cek kembali URL Apps Script Anda.")

# --- SIDEBAR & NAVIGASI ---
with st.sidebar:
    st.markdown("## 🏢 Dashboard KI")
    menu = st.selectbox("Navigasi", ["📍 Absensi", "📊 Rekap Absensi"])
    st.divider()
    waktu_skrg = datetime.datetime.now() + datetime.timedelta(hours=7)
    st.markdown(f'<div class="sidebar-time-box">📅 <b>{waktu_skrg.strftime("%d %B %Y")}</b><br>⏰ <b>{waktu_skrg.strftime("%H:%M:%S")} WIB</b></div>', unsafe_allow_html=True)

if menu == "📍 Absensi":
    status_sesi = "TUTUP"
    if 6 <= waktu_skrg.hour < 12: status_sesi = "MASUK"
    elif 13 <= waktu_skrg.hour < 22: status_sesi = "PULANG"
    halaman_presensi(waktu_skrg, status_sesi, waktu_skrg.strftime("%Y-%m-%d"))
else:
    halaman_rekap(waktu_skrg)
