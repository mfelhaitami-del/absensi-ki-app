import streamlit as st
import pandas as pd
import datetime
import requests
import time
from PIL import Image, ImageOps
from io import BytesIO

# --- KONFIGURASI ---
# Ganti dengan API Key ImgBB dan URL Web App Google Script Anda
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbyHMhEr0zy226CjIzHEGQJL0PUsMO3AI6EtZGUOTtDEX6DSqOKaRRrG1EE-eyVxXZES/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# --- CUSTOM CSS (PREMIUM & NON-MIRROR CAMERA) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] { background-color: #1e293b !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    
    /* Hero Title & Subtitle */
    .hero-title { 
        font-size: 60px; font-weight: 800; color: #ffffff !important; 
        text-align: center; text-shadow: 2px 2px 8px rgba(0,0,0,0.5); margin-bottom: 0px; 
    }
    .hero-subtitle { font-size: 18px; color: #cbd5e1 !important; text-align: center; margin-bottom: 30px; }
    .welcome-text { font-size: 28px; font-weight: 600; color: #ffffff !important; margin-bottom: 10px; }
    
    /* FIX NON-MIRROR CAMERA: Anda ke kanan, layar ikut ke kanan */
    video { 
        transform: scaleX(-1) !important; 
        -webkit-transform: scaleX(-1) !important; 
        border-radius: 20px; border: 3px solid #3b82f6; 
    }
    [data-testid="stCameraInput"] video {
        transform: scaleX(-1) !important;
        -webkit-transform: scaleX(-1) !important;
    }
    
    /* Button Styling */
    div.stButton > button { 
        width: 100%; border-radius: 12px; height: 3.5em; 
        background-color: #3b82f6; color: white !important; 
        font-weight: 700; font-size: 16px; border: none;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
    }
    
    /* Sidebar Time Box */
    .sidebar-time-box {
        background-color: rgba(255,255,255,0.1); padding: 12px;
        border-radius: 10px; margin-top: 10px; border: 1px solid rgba(255,255,255,0.2);
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI HALAMAN PRESENSI ---
def halaman_presensi(waktu_aktif, status_absen, tgl_skrg):
    st.markdown('<p class="hero-title">Absensi Tim KI</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">Sistem Pencatatan Kehadiran Digital Real-Time</p>', unsafe_allow_html=True)
    
    if status_absen == "TUTUP":
        st.error(f"🚫 Sesi absensi tutup. (Sekarang: {waktu_aktif.strftime('%H:%M:%S')} WIB)")
    else:
        daftar_nama = [
            "Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", 
            "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", 
            "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"
        ]
        nama_lengkap = st.selectbox("Pilih nama Anda:", daftar_nama, key="p_nama")
        
        st.markdown(f'<p class="welcome-text">Halo, {nama_lengkap}! 👋</p>', unsafe_allow_html=True)
        st.info(f"📍 Sesi: **Absen {status_absen}**")
        
        # Input Kamera (Tampilan Visual Non-Mirror via CSS)
        foto = st.camera_input("Ambil foto wajah untuk verifikasi", key="p_cam")

        if st.button(f"🚀 Kirim Absensi {status_absen} Sekarang", key="p_btn"):
            if foto:
                with st.spinner("Sedang memproses data..."):
                    try:
                        img = Image.open(foto)
                        # Hasil foto asli biasanya sudah real, jadi tidak perlu ImageOps.mirror lagi
                        # jika ingin hasil yang disimpan sama dengan visual yang sudah di-fix CSS.
                        img_final = img 
                        
                        buf = BytesIO()
                        img_final.save(buf, format="JPEG")
                        
                        # 1. Upload ke ImgBB
                        files = {"image": buf.getvalue()}
                        resp = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files=files)
                        link_foto = resp.json()["data"]["url"]
                        
                        # 2. Kirim ke Google Sheets
                        payload = {
                            "nama": nama_lengkap, "tanggal": tgl_skrg, 
                            "jam": waktu_aktif.strftime("%H:%M:%S"), 
                            "status": status_absen, "foto_link": link_foto
                        }
                        requests.post(WEBAPP_URL, json=payload)
                        
                        st.success(f"🎉 Berhasil! Terima kasih {nama_lengkap}, data sudah tersimpan.")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Terjadi kesalahan: {e}")
            else:
                st.warning("⚠️ Ambil foto terlebih dahulu!")

# --- FUNGSI HALAMAN REKAP ---
def halaman_rekap(waktu_aktif):
    st.markdown('<p class="hero-title" style="font-size:40px;">Rekap Data Bulanan</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">Laporan Kehadiran Berdasarkan Database</p>', unsafe_allow_html=True)
    
    bulan_indo = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    
    c1, c2 = st.columns(2)
    with c1: p_bulan = st.selectbox("Pilih Bulan", bulan_indo, index=waktu_aktif.month - 1, key="r_bln")
    with c2: p_tahun = st.selectbox("Pilih Tahun", [2025, 2026, 2027], index=1, key="r_thn")
    
    if st.button("🔍 Tampilkan Data Laporan", key="r_btn"):
        st.cache_data.clear()
        nama_tab = f"{p_bulan} {p_tahun}"
        try:
            res = requests.get(f"{WEBAPP_URL}?bulan={nama_tab}")
            data_json = res.json()
            if data_json:
                df = pd.DataFrame(data_json)
                # Rapikan format tanggal & jam
                df[df.columns[1]] = pd.to_datetime(df[df.columns[1]], errors='coerce').dt.strftime('%d-%m-%Y')
                for i in [2, 3]:
                    df[df.columns[i]] = pd.to_datetime(df[df.columns[i]], errors='coerce').dt.strftime('%H:%M:%S')
                df = df.fillna("-")
                df.columns = ["Nama", "Tanggal", "Jam Masuk", "Jam Pulang", "Link Foto"]
                
                st.write(f"### 📋 Laporan: {nama_tab}")
                st.dataframe(df, use_container_width=True)
            else:
                st.info(f"ℹ️ Belum ada data untuk bulan {nama_tab}.")
        except:
            st.error("❌ Gagal terhubung ke database.")

# --- LOGIKA UTAMA (MAIN) ---
with st.sidebar:
    st.markdown("## 🏢 Dashboard KI")
    menu = st.selectbox("Navigasi", ["📍 Presensi", "📊 Rekap Absensi"], key="nav_menu")
    st.divider()
    
    # Ambil waktu WIB
    waktu_skrg = datetime.datetime.now() + datetime.timedelta(hours=7)
    
    # Tampilan Waktu 2 Baris di Sidebar
    st.markdown(f"""
    <div class="sidebar-time-box">
        📅 <b>{waktu_skrg.strftime('%d %B %Y')}</b><br>
        ⏰ <b>{waktu_skrg.strftime('%H:%M:%S')} WIB</b>
    </div>
    """, unsafe_allow_html=True)

# Variabel Sesi
tgl_cek = waktu_skrg.strftime("%Y-%m-%d")
status_sesi = "TUTUP"
if 6 <= waktu_skrg.hour < 12: status_sesi = "MASUK"
elif 13 <= waktu_skrg.hour < 18: status_sesi = "PULANG"

# Routing Menu
if menu == "📍 Presensi":
    halaman_presensi(waktu_skrg, status_sesi, tgl_cek)
    # Auto-refresh jam hanya aktif di menu Presensi
    time.sleep(1)
    st.rerun()
else:
    # Menu Rekap statis (Tanpa rerun agar tidak bug/loading terus)
    halaman_rekap(waktu_skrg)
