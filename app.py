import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image, ImageOps
from io import BytesIO

# --- KONFIGURASI ---
# Pastikan URL Web App dari Apps Script sudah benar
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbyHMhEr0zy226CjIzHEGQJL0PUsMO3AI6EtZGUOTtDEX6DSqOKaRRrG1EE-eyVxXZES/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# --- CUSTOM CSS UNTUK TAMPILAN PROFESIONAL ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #f0f2f6; }
    .main-title {
        font-size: 35px; font-weight: bold; color: #1E3A8A;
        text-align: center; margin-bottom: 20px;
    }
    .metric-container {
        background-color: white; padding: 15px; border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center;
    }
    video { -webkit-transform: scaleX(1) !important; transform: scaleX(1) !important; }
    </style>
""", unsafe_allow_html=True)

# Waktu Sekarang (WIB)
waktu_now = datetime.datetime.now() + datetime.timedelta(hours=7)
tgl_skrg = waktu_now.strftime("%Y-%m-%d")
jam_skrg_int = waktu_now.hour
bulan_indo = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]

# --- SIDEBAR BRANDING ---
st.sidebar.markdown("## 🏢 Menu Utama")
menu = st.sidebar.selectbox("Pilih Navigasi", ["📍 Presensi", "📊 Rekap Absensi"])
st.sidebar.write("---")
st.sidebar.info(f"📅 {waktu_now.strftime('%d %B %Y')}\n\n⏰ {waktu_now.strftime('%H:%M:%S')} WIB")

# --- LOGIKA PENENTUAN STATUS ---
status_absen = None
if 6 <= jam_skrg_int < 12:
    status_absen = "MASUK"
elif 13 <= jam_skrg_int < 18:
    status_absen = "PULANG"
else:
    status_absen = "TUTUP"

# --- HALAMAN PRESENSI ---
if menu == "📍 Presensi":
    st.markdown('<p class="main-title">📸 Absensi Foto Real-Time</p>', unsafe_allow_html=True)
    
    if status_absen == "TUTUP":
        st.warning("🚫 Sistem Absensi Sedang Tutup. (Buka: 06:00-12:00 & 13:00-18:00)")
    else:
        st.success(f"✅ Sesi Absen **{status_absen}** Aktif")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.write("### Data Diri")
            daftar_nama = [
                "Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", 
                "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", 
                "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"
            ]
            nama = st.selectbox("Pilih Nama Anda", daftar_nama)
            st.write(f"Status: **Absen {status_absen}**")
            
            btn_kirim = st.button(f"🚀 Kirim Absensi {status_absen}", use_container_width=True)

        with col2:
            st.write("### Ambil Foto")
            foto = st.camera_input("Pastikan wajah terlihat jelas")

        if btn_kirim:
            if foto:
                with st.spinner("Sedang memproses data..."):
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
                        st.success(f"🎉 Berhasil! Absensi {status_absen} untuk {nama} telah tercatat.")
                    except Exception as e:
                        st.error(f"Terjadi kesalahan teknis: {e}")
            else:
                st.warning("Silakan ambil foto terlebih dahulu melalui kamera!")

# --- HALAMAN REKAP ---
elif menu == "📊 Rekap Absensi":
    st.markdown('<p class="main-title">📊 Rekap Absensi Bulanan</p>', unsafe_allow_html=True)
    
    # Filter Pemilihan Bulan & Tahun
    c1, c2 = st.columns(2)
    with c1:
        p_bulan = st.selectbox("Pilih Bulan", bulan_indo, index=waktu_now.month - 1)
    with c2:
        p_tahun = st.selectbox("Pilih Tahun", [2025, 2026, 2027], index=1)
    
    nama_tab_target = f"{p_bulan} {p_tahun}"
    
    if st.button("🔍 Tampilkan Data"):
        st.cache_data.clear()
        with st.spinner(f"Mengambil data {nama_tab_target}..."):
            try:
                res = requests.get(f"{WEBAPP_URL}?bulan={nama_tab_target}")
                data_json = res.json()
                
                if data_json:
                    df = pd.DataFrame(data_json)
                    df.columns = ["Nama", "Tanggal", "Jam Masuk", "Jam Pulang", "Link Foto"]
                    st.dataframe(df, use_container_width=True)
                    
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Download Laporan (CSV)", csv, f"Rekap_{nama_tab_target}.csv", "text/csv")
                else:
                    st.info(f"Belum ada data absensi untuk bulan {nama_tab_target}.")
            except:
                st.error("Gagal terhubung ke database. Pastikan URL Web App sudah benar.")
