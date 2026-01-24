import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image, ImageOps
from io import BytesIO

# --- KONFIGURASI ---
# Ganti dengan API Key ImgBB dan URL Web App Google Script Anda
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbyHMhEr0zy226CjIzHEGQJL0PUsMO3AI6EtZGUOTtDEX6DSqOKaRRrG1EE-eyVxXZES/exec"

st.set_page_config(page_title="Absensi Tim KI Satker PPS Banten", layout="wide")

# --- CUSTOM CSS (PREMIUM UI & DARK MODE SUPPORT) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #1e293b !important;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Hero Section */
    .hero-title {
        font-size: 65px;
        font-weight: 800;
        color: #ffffff !important;
        text-align: center;
        margin-bottom: 0px;
        text-shadow: 2px 2px 8px rgba(0,0,0,0.5);
    }
    
    .hero-subtitle {
        font-size: 20px;
        color: #cbd5e1 !important;
        text-align: center;
        margin-bottom: 40px;
    }

    /* Welcome Text */
    .welcome-text {
        font-size: 30px;
        font-weight: 600;
        color: #ffffff !important;
        margin-top: 10px;
        margin-bottom: 10px;
        text-align: left;
    }

    /* Fix Camera Mirror */
    video { 
        -webkit-transform: scaleX(1) !important; 
        transform: scaleX(1) !important; 
        border-radius: 20px;
        border: 3px solid #3b82f6;
    }

    /* Button Styling */
    div.stButton > button {
        width: 100%;
        border-radius: 15px;
        height: 3.8em;
        background-color: #3b82f6;
        color: white !important;
        font-weight: 700;
        font-size: 18px;
        border: none;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
        transition: 0.3s;
    }
    div.stButton > button:hover {
        background-color: #2563eb;
        transform: translateY(-2px);
    }

    /* Selectbox Labels */
    label {
        color: white !important;
        font-size: 16px !important;
    }
    </style>
""", unsafe_allow_html=True)

# Logika Waktu (WIB)
waktu_now = datetime.datetime.now() + datetime.timedelta(hours=7)
tgl_skrg = waktu_now.strftime("%Y-%m-%d")
jam_skrg_int = waktu_now.hour
bulan_indo = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]

# --- SIDEBAR ---
st.sidebar.markdown("## 🏢 Dashboard KI")
menu = st.sidebar.selectbox("Navigasi", ["📍 Absensi", "📊 Rekap Absensi"])
st.sidebar.divider()
st.sidebar.write(f"📅 **{waktu_now.strftime('%d %B %Y')}**")
st.sidebar.write(f"⏰ **{waktu_now.strftime('%H:%M:%S')} WIB**")

# Logika Sesi Absensi
status_absen = "TUTUP"
if 6 <= jam_skrg_int < 12: status_absen = "MASUK"
elif 13 <= jam_skrg_int < 18: status_absen = "PULANG"

# --- HALAMAN PRESENSI ---
if menu == "📍 Absensi":
    st.markdown('<p class="hero-title">Absensi Tim KI</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">Sistem Pencatatan Kehadiran Digital Real-Time</p>', unsafe_allow_html=True)
    
    if status_absen == "TUTUP":
        st.error("🚫 Maaf, sesi absensi saat ini sedang ditutup (Buka: 06:00-12:00 & 13:00-18:00).")
    else:
        daftar_nama = ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"]
        
        # Form Identitas
        nama = st.selectbox("Pilih nama Anda di bawah ini:", daftar_nama)
        st.markdown(f'<p class="welcome-text">Halo, {nama.split()[0]}! 👋</p>', unsafe_allow_html=True)
        
        st.info(f"📍 Anda sedang melakukan sesi **Absen {status_absen}**")

        # Input Kamera
        foto = st.camera_input("Ambil foto wajah untuk verifikasi")

        # Tombol Kirim di Paling Bawah
        if st.button(f"🚀 Kirim Absensi {status_absen}"):
            if foto:
                with st.spinner("Sedang memproses dan mengirim data..."):
                    try:
                        # Olah foto agar tidak mirror
                        img = Image.open(foto)
                        img_real = ImageOps.mirror(img)
                        buf = BytesIO()
                        img_real.save(buf, format="JPEG")
                        
                        # 1. Upload ke ImgBB
                        files = {"image": buf.getvalue()}
                        resp = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files=files)
                        link_foto = resp.json()["data"]["url"]

                        # 2. Kirim ke Google Sheets
                        payload = {
                            "nama": nama, "tanggal": tgl_skrg, 
                            "jam": waktu_now.strftime("%H:%M:%S"),
                            "status": status_absen, "foto_link": link_foto
                        }
                        requests.post(WEBAPP_URL, json=payload)
                        st.success(f"🎉 Berhasil! Terima kasih {nama.split()[0]}, absensi {status_absen} Anda telah tercatat.")
                    except Exception as e:
                        st.error(f"Gagal mengirim data: {e}")
            else:
                st.warning("⚠️ Silakan ambil foto terlebih dahulu!")

# --- HALAMAN REKAP ---
elif menu == "📊 Rekap Absensi":
    st.markdown('<p class="hero-title" style="font-size:45px;">Rekap Data Bulanan</p>', unsafe_allow_html=True)
    
    # Filter Pemilihan
    c1, c2 = st.columns(2)
    with c1: p_bulan = st.selectbox("Pilih Bulan", bulan_indo, index=waktu_now.month - 1)
    with c2: p_tahun = st.selectbox("Pilih Tahun", [2025, 2026, 2027], index=1)
    
    nama_tab_target = f"{p_bulan} {p_tahun}"
    
    if st.button("🔍 Tampilkan Data"):
        st.cache_data.clear()
        try:
            res = requests.get(f"{WEBAPP_URL}?bulan={nama_tab_target}")
            data_json = res.json()
            if data_json:
                df = pd.DataFrame(data_json)
                
                # Pembersihan Format Tanggal & Jam
                df[df.columns[1]] = pd.to_datetime(df[df.columns[1]], errors='coerce').dt.strftime('%d-%m-%Y')
                for col_idx in [2, 3]:
                    df[df.columns[col_idx]] = pd.to_datetime(df[df.columns[col_idx]], errors='coerce').dt.strftime('%H:%M:%S')
                
                df = df.fillna("-")
                df.columns = ["Nama", "Tanggal", "Jam Masuk", "Jam Pulang", "Link Foto"]
                
                st.write(f"### 📋 Laporan Kehadiran: {nama_tab_target}")
                st.dataframe(df, use_container_width=True)
                
                # Download Button
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Laporan (CSV)", csv, f"Rekap_{nama_tab_target}.csv", "text/csv")
            else:
                st.info(f"ℹ️ Belum ada data absensi untuk bulan {nama_tab_target}.")
        except:
            st.error("Gagal mengambil data dari database.")
