import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image, ImageOps
from io import BytesIO

# --- KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbyHMhEr0zy226CjIzHEGQJL0PUsMO3AI6EtZGUOTtDEX6DSqOKaRRrG1EE-eyVxXZES/exec"

st.set_page_config(page_title="Absensi Tim KI Satker PPS Banten", layout="wide")

# --- CUSTOM CSS (DIPERBARUI UNTUK KONTRAS TINGGI) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }
    
    /* Memperbaiki Sidebar agar Teks Terlihat (Background Gelap, Teks Putih) */
    [data-testid="stSidebar"] {
        background-color: #1e293b !important;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Judul Sangat Besar & Warna Putih */
    .hero-title {
        font-size: 65px; /* Ukuran diperbesar */
        font-weight: 800;
        color: #ffffff !important; /* Warna Putih */
        text-align: center;
        margin-bottom: 0px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .hero-subtitle {
        font-size: 20px;
        color: #e2e8f0 !important; /* Abu-abu sangat terang */
        text-align: center;
        margin-bottom: 30px;
    }

    /* Styling Sapaan Putih */
    .welcome-text {
        font-size: 28px;
        font-weight: 600;
        color: #ffffff !important; /* Warna Putih */
        margin-top: 10px;
        margin-bottom: 20px;
    }

    /* Mengatur warna label input agar putih */
    label {
        color: white !important;
    }

    /* Mematikan Mirror Kamera */
    video { 
        -webkit-transform: scaleX(1) !important; 
        transform: scaleX(1) !important; 
        border-radius: 15px;
        border: 2px solid #3b82f6;
    }

    /* Tombol Biru Terang agar Standout */
    div.stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 3.5em;
        background-color: #3b82f6;
        color: white !important;
        font-weight: 700;
        font-size: 18px;
        border: none;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
    }
    </style>
""", unsafe_allow_html=True)

# Waktu Sekarang (WIB)
waktu_now = datetime.datetime.now() + datetime.timedelta(hours=7)
tgl_skrg = waktu_now.strftime("%Y-%m-%d")
jam_skrg_int = waktu_now.hour
bulan_indo = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]

# --- SIDEBAR ---
st.sidebar.markdown("## 🏢 Dashboard Absensi KI")
menu = st.sidebar.selectbox("Navigasi", ["📍 Absensi", "📊 Rekap Absensi"])
st.sidebar.divider()
st.sidebar.write(f"📅 **{waktu_now.strftime('%d %B %Y')}**")
st.sidebar.write(f"⏰ **{waktu_now.strftime('%H:%M:%S')} WIB**")

# Logika Sesi
status_absen = "TUTUP"
if 6 <= jam_skrg_int < 12: status_absen = "MASUK"
elif 13 <= jam_skrg_int < 18: status_absen = "PULANG"

# --- HALAMAN PRESENSI ---
if menu == "📍 Absensi":
    st.markdown('<p class="hero-title">Absensi Tim KI</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">Pastikan kehadiran Anda tercatat dengan benar hari ini.</p>', unsafe_allow_html=True)
    
    if status_absen == "TUTUP":
        st.error("🚫 Maaf, sesi absensi saat ini sedang ditutup.")
    else:
        daftar_nama = ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"]
        
        # Form Input
        nama = st.selectbox("Siapa yang hadir hari ini?", daftar_nama)
        st.markdown(f'<p class="welcome-text">Halo, {nama.split()[0]}! 👋</p>', unsafe_allow_html=True)
        
        st.info(f"📍 Anda sedang melakukan absensi **{status_absen}**")

        foto = st.camera_input("Ambil Foto Wajah")

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

                        payload = {
                            "nama": nama, "tanggal": tgl_skrg, 
                            "jam": waktu_now.strftime("%H:%M:%S"),
                            "status": status_absen, "foto_link": link_foto
                        }
                        requests.post(WEBAPP_URL, json=payload)
                        st.success(f"Berhasil! Terima kasih {nama.split()[0]}, datamu sudah masuk.")
                    except:
                        st.error("Gagal mengirim data. Cek koneksi internet.")
            else:
                st.warning("Ambil foto terlebih dahulu!")

# --- HALAMAN REKAP ---
elif menu == "📊 Rekap Absensi":
    st.markdown('<p class="hero-title" style="font-size:45px;">Rekap Data Bulanan</p>', unsafe_allow_html=True)
    # Filter dan Tabel akan mengikuti tema otomatis Streamlit
    c1, c2 = st.columns(2)
    with c1: p_bulan = st.selectbox("Bulan", bulan_indo, index=waktu_now.month - 1)
    with c2: p_tahun = st.selectbox("Tahun", [2025, 2026, 2027], index=1)
    
    nama_tab_target = f"{p_bulan} {p_tahun}"
    
    if st.button("🔍 Lihat Data"):
        st.cache_data.clear()
        try:
            res = requests.get(f"{WEBAPP_URL}?bulan={nama_tab_target}")
            data_json = res.json()
            if data_json:
                df = pd.DataFrame(data_json)
                df.columns = ["Nama", "Tanggal", "Jam Masuk", "Jam Pulang", "Link Foto"]
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Data belum tersedia untuk bulan ini.")
        except:
            st.error("Gagal mengambil data.")


