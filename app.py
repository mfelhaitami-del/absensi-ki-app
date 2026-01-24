import streamlit as st
import pandas as pd
import datetime
import requests
import time  # Tambahan untuk jam berjalan
from PIL import Image, ImageOps
from io import BytesIO

# --- KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbyHMhEr0zy226CjIzHEGQJL0PUsMO3AI6EtZGUOTtDEX6DSqOKaRRrG1EE-eyVxXZES/exec"

st.set_page_config(page_title="Absensi Tim KI Satker PPS Banten", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    .hero-title { font-size: 65px; font-weight: 800; color: #ffffff !important; text-align: center; text-shadow: 2px 2px 8px rgba(0,0,0,0.5); margin-bottom: 0px; }
    .hero-subtitle { font-size: 20px; color: #cbd5e1 !important; text-align: center; margin-bottom: 40px; }
    .welcome-text { font-size: 30px; font-weight: 600; color: #ffffff !important; margin-bottom: 10px; }
    video { -webkit-transform: scaleX(1) !important; transform: scaleX(1) !important; border-radius: 20px; border: 3px solid #3b82f6; }
    div.stButton > button { width: 100%; border-radius: 15px; height: 3.8em; background-color: #3b82f6; color: white !important; font-weight: 700; font-size: 18px; border: none; box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4); }
    label { color: white !important; font-size: 16px !important; }
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI JAM BERJALAN DI SIDEBAR ---
def update_sidebar_time():
    with st.sidebar:
        st.markdown("## 🏢 Dashboard KI")
        # Placeholder untuk jam agar tidak menumpuk saat refresh
        clock_placeholder = st.empty()
        
    # Ambil waktu WIB
    waktu_now = datetime.datetime.now() + datetime.timedelta(hours=7)
    clock_placeholder.markdown(f"""
    ---
    📅 **{waktu_now.strftime('%d %B %Y')}** ⏰ **{waktu_now.strftime('%H:%M:%S')} WIB**
    """)
    return waktu_now

# Inisialisasi Sidebar & Ambil Waktu
menu = st.sidebar.selectbox("Navigasi", ["📍 Absensi", "📊 Rekap Absensi"])
waktu_aktif = update_sidebar_time()

# Logika Sesi
tgl_skrg = waktu_aktif.strftime("%Y-%m-%d")
jam_int = waktu_aktif.hour
status_absen = "TUTUP"
if 6 <= jam_int < 12: status_absen = "Masuk"
elif 13 <= jam_int < 18: status_absen = "Pulang"

# --- HALAMAN PRESENSI ---
if menu == "📍 Absensi":
    st.markdown('<p class="hero-title">Absensi Tim KI</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">Sistem Pencatatan Kehadiran Digital Real-Time</p>', unsafe_allow_html=True)
    
    if status_absen == "TUTUP":
        st.error(f"Maaf, sesi absensi sedang ditutup. (Sekarang: {waktu_aktif.strftime('%H:%M:%S')})")
    else:
        daftar_nama = ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"]
        nama = st.selectbox("Pilih nama Anda di bawah ini:", daftar_nama)
        st.markdown(f'<p class="welcome-text">Halo, {nama.split()[0]}! 👋</p>', unsafe_allow_html=True)
        st.info(f"Anda sedang melakukan sesi **Absen {status_absen}**")

        foto = st.camera_input("Ambil foto wajah untuk verifikasi")

        if st.button(f"Kirim Absensi {status_absen}"):
            if foto:
                with st.spinner("Mengirim data..."):
                    try:
                        img = Image.open(foto)
                        img_real = ImageOps.mirror(img)
                        buf = BytesIO()
                        img_real.save(buf, format="JPEG")
                        files = {"image": buf.getvalue()}
                        resp = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files=files)
                        link_foto = resp.json()["data"]["url"]
                        payload = {"nama": nama, "tanggal": tgl_skrg, "jam": waktu_aktif.strftime("%H:%M:%S"), "status": status_absen, "foto_link": link_foto}
                        requests.post(WEBAPP_URL, json=payload)
                        st.success(f"Berhasil! Terima kasih {nama.split()[0]}, data sudah masuk.")
                    except:
                        st.error("Gagal mengirim data.")
            else:
                st.warning("Ambil foto dulu!")

# --- HALAMAN REKAP ---
elif menu == "📊 Rekap Absensi":
    st.markdown('<p class="hero-title" style="font-size:45px;">Rekap Data Bulanan</p>', unsafe_allow_html=True)
    bulan_indo = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    c1, c2 = st.columns(2)
    with c1: p_bulan = st.selectbox("Bulan", bulan_indo, index=waktu_aktif.month - 1)
    with c2: p_tahun = st.selectbox("Tahun", [2025, 2026, 2027], index=1)
    
    if st.button("🔍 Tampilkan Data"):
        st.cache_data.clear()
        nama_tab = f"{p_bulan} {p_tahun}"
        try:
            res = requests.get(f"{WEBAPP_URL}?bulan={nama_tab}")
            data_json = res.json()
            if data_json:
                df = pd.DataFrame(data_json)
                df[df.columns[1]] = pd.to_datetime(df[df.columns[1]], errors='coerce').dt.strftime('%d-%m-%Y')
                for i in [2, 3]: df[df.columns[i]] = pd.to_datetime(df[df.columns[i]], errors='coerce').dt.strftime('%H:%M:%S')
                df = df.fillna("-")
                df.columns = ["Nama", "Tanggal", "Jam Masuk", "Jam Pulang", "Link Foto"]
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Data kosong.")
        except:
            st.error("Gagal muat data.")

# --- TRICK UNTUK JAM BERJALAN (AUTO REFRESH SETIAP 1 DETIK) ---
# Tambahkan ini di paling bawah agar jam di sidebar terus update
time.sleep(1)
st.rerun()
