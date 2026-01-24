import streamlit as st
import pandas as pd
import datetime
import requests
import time
from PIL import Image, ImageOps
from io import BytesIO

# --- KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbyHMhEr0zy226CjIzHEGQJL0PUsMO3AI6EtZGUOTtDEX6DSqOKaRRrG1EE-eyVxXZES/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    .hero-title { font-size: 60px; font-weight: 800; color: #ffffff !important; text-align: center; margin-bottom: 0px; }
    .hero-subtitle { font-size: 18px; color: #cbd5e1 !important; text-align: center; margin-bottom: 30px; }
    .welcome-text { font-size: 28px; font-weight: 600; color: #ffffff !important; margin-bottom: 10px; }
    video { -webkit-transform: scaleX(1) !important; transform: scaleX(1) !important; border-radius: 20px; border: 3px solid #3b82f6; }
    div.stButton > button { width: 100%; border-radius: 12px; height: 3.5em; background-color: #3b82f6; color: white !important; font-weight: 700; }
    .sidebar-time-box { background-color: rgba(255,255,255,0.1); padding: 10px; border-radius: 10px; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI HALAMAN PRESENSI ---
def halaman_presensi(waktu_aktif, status_absen, tgl_skrg):
    st.markdown('<p class="hero-title">Absensi Tim KI</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">Sistem Pencatatan Kehadiran Digital Real-Time</p>', unsafe_allow_html=True)
    
    if status_absen == "TUTUP":
        st.error(f"🚫 Maaf, sesi absensi sedang ditutup. (Sekarang: {waktu_aktif.strftime('%H:%M:%S')})")
    else:
        daftar_nama = ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"]
        nama_lengkap = st.selectbox("Pilih nama Anda:", daftar_nama, key="sel_nama_p")
        
        st.markdown(f'<p class="welcome-text">Halo, {nama_lengkap}! 👋</p>', unsafe_allow_html=True)
        st.info(f"📍 Sesi aktif: **Absen {status_absen}**")
        
        foto = st.camera_input("Ambil foto wajah", key="cam_p")

        if st.button(f"🚀 Kirim Absensi {status_absen}", key="btn_p"):
            if foto:
                with st.spinner("Proses kirim..."):
                    try:
                        img = Image.open(foto)
                        img_real = ImageOps.mirror(img)
                        buf = BytesIO()
                        img_real.save(buf, format="JPEG")
                        files = {"image": buf.getvalue()}
                        resp = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files=files)
                        link_foto = resp.json()["data"]["url"]
                        
                        payload = {"nama": nama_lengkap, "tanggal": tgl_skrg, "jam": waktu_aktif.strftime("%H:%M:%S"), "status": status_absen, "foto_link": link_foto}
                        requests.post(WEBAPP_URL, json=payload)
                        st.success(f"Berhasil! Data {nama_lengkap} sudah tersimpan.")
                    except:
                        st.error("Gagal mengirim data.")
            else:
                st.warning("Ambil foto dulu!")

# --- FUNGSI HALAMAN REKAP ---
def halaman_rekap(waktu_aktif):
    st.markdown('<p class="hero-title" style="font-size:40px;">Rekap Data Bulanan</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">Laporan Kehadiran Berdasarkan Database</p>', unsafe_allow_html=True)
    
    bulan_indo = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    c1, c2 = st.columns(2)
    with c1: p_bulan = st.selectbox("Pilih Bulan", bulan_indo, index=waktu_aktif.month - 1, key="r_bln")
    with c2: p_tahun = st.selectbox("Pilih Tahun", [2025, 2026, 2027], index=1, key="r_thn")
    
    if st.button("🔍 Tampilkan Data", key="r_btn"):
        nama_tab = f"{p_bulan} {p_tahun}"
        try:
            res = requests.get(f"{WEBAPP_URL}?bulan={nama_tab}")
            data_json = res.json()
            if data_json:
                df = pd.DataFrame(data_json)
                # Format Tanggal
                df[df.columns[1]] = pd.to_datetime(df[df.columns[1]], errors='coerce').dt.strftime('%d-%m-%Y')
                # Format Jam
                for i in [2, 3]:
                    df[df.columns[i]] = pd.to_datetime(df[df.columns[i]], errors='coerce').dt.strftime('%H:%M:%S')
                df = df.fillna("-")
                df.columns = ["Nama", "Tanggal", "Jam Masuk", "Jam Pulang", "Link Foto"]
                st.dataframe(df, use_container_width=True)
            else:
                st.info(f"Tidak ada data untuk {nama_tab}.")
        except:
            st.error("Koneksi database terputus.")

# --- LOGIKA UTAMA ---
with st.sidebar:
    st.markdown("## 🏢 Dashboard KI")
    menu = st.selectbox("Navigasi", ["📍 Presensi", "📊 Rekap Absensi"], key="nav_menu")
    st.divider()
    waktu_aktif = datetime.datetime.now() + datetime.timedelta(hours=7)
    st.markdown(f"""
    <div class="sidebar-time-box">
        📅 <b>{waktu_aktif.strftime('%d %B %Y')}</b><br>
        ⏰ <b>{waktu_aktif.strftime('%H:%M:%S')} WIB</b>
    </div>
    """, unsafe_allow_html=True)

# Parameter Waktu
tgl_skrg = waktu_aktif.strftime("%Y-%m-%d")
status_absen = "TUTUP"
if 6 <= waktu_aktif.hour < 12: status_absen = "MASUK"
elif 13 <= waktu_aktif.hour < 18: status_absen = "PULANG"

# --- ROUTING HALAMAN ---
if menu == "📍 Presensi":
    halaman_presensi(waktu_aktif, status_absen, tgl_skrg)
    # Jalankan Auto-refresh HANYA di halaman presensi agar jam berdetak
    time.sleep(1)
    st.rerun()
else:
    # Halaman Rekap TIDAK menggunakan st.rerun() agar tidak bug/loading terus
    halaman_rekap(waktu_aktif)
