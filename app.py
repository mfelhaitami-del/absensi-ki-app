import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image
import io
import numpy as np

# --- 1. KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
# MASUKKAN URL WEB APP BARU ANDA DI SINI
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxeekYyGnEeCHTIUW-V1TlQRwJImSWbDfHzEuUtKoKZJ7skejcSCkiD30oPk5qQfAcP/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# --- 2. CSS CUSTOM ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
    
    /* Mirroring Camera Fix */
    [data-testid="stCameraInput"] video, [data-testid="stCameraInput"] img {
        transform: scaleX(-1);
    }

    .stApp {
        background: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.6)), 
                    url("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Logo_PU_%28RGB%29.jpg/960px-Logo_PU_%28RGB%29.jpg");
        background-size: cover; background-position: center; background-attachment: fixed;
    }
    
    [data-testid="stSidebar"] { background-color: rgba(15, 23, 42, 0.9) !important; backdrop-filter: blur(10px); }
    [data-testid="stSidebar"] * { color: white !important; }
    
    .sidebar-time-box { 
        background-color: rgba(255,255,255,0.1); padding: 15px; border-radius: 12px; 
        text-align: center; border: 1px solid #3b82f6; margin-bottom: 20px;
    }

    .hero-title { 
        font-size: 30px; font-weight: 800; text-align: center; color: white; margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. JAM WIB ---
@st.fragment(run_every="1s")
def jam_sidebar():
    # Streamlit Cloud biasanya pakai UTC, tambahkan 7 jam untuk WIB
    waktu_skrg = datetime.datetime.now() + datetime.timedelta(hours=7)
    st.markdown(f"""
    <div class="sidebar-time-box">
        <span style="font-size: 14px;">{waktu_skrg.strftime('%d %B %Y')}</span><br>
        <span style="font-size: 28px; color: #3b82f6; font-weight: bold;">{waktu_skrg.strftime('%H:%M:%S')}</span><br>
        <b>WIB</b>
    </div>
    """, unsafe_allow_html=True)
    return waktu_skrg

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("### 🏢 MENU UTAMA")
    menu = st.selectbox("Pilih Layanan:", ["📍 Absensi", "📊 Rekap Absensi"])
    st.divider()
    waktu_aktif = jam_sidebar()

# --- 5. HALAMAN ABSENSI ---
if menu == "📍 Absensi":
    st.markdown('<p class="hero-title">Absensi Tim KI Satker PPS Banten</p>', unsafe_allow_html=True)
    
    # Penentuan Sesi
    if 6 <= waktu_aktif.hour < 12: status_sesi = "MASUK"
    elif 12 <= waktu_aktif.hour < 23: status_sesi = "PULANG"
    else: status_sesi = "TUTUP"
    
    if status_sesi == "TUTUP":
        st.error("🚫 Maaf, Sesi Absensi Masuk/Pulang sedang ditutup.")
    else:
        st.info(f"Sesi Aktif: **Absen {status_sesi}**")
        nama = st.selectbox("Pilih Nama:", ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"])
        foto_raw = st.camera_input("Ambil Foto Wajah")
        
        if st.button("KIRIM DATA ABSENSI", use_container_width=True):
            if foto_raw:
                with st.spinner("Sedang memproses data..."):
                    try:
                        # Balik foto secara fisik agar tidak mirror
                        img = Image.open(foto_raw).convert("RGB")
                        flipped_img = Image.fromarray(np.flip(np.array(img), axis=1))
                        
                        buf = io.BytesIO()
                        flipped_img.save(buf, format="JPEG")
                        
                        # 1. Upload ke ImgBB
                        res_img = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": buf.getvalue()}).json()
                        link_foto = res_img["data"]["url"]
                        
                        # 2. Kirim ke GSheets
                        payload = {
                            "nama": nama, 
                            "tanggal": waktu_aktif.strftime("%Y-%m-%d"), 
                            "jam": waktu_aktif.strftime("%H:%M:%S"), 
                            "status": status_sesi, 
                            "foto_link": link_foto
                        }
                        requests.post(WEBAPP_URL, json=payload, timeout=20)
                        
                        st.success(f"✅ Absen {status_sesi} Berhasil dikirim!")
                        
                    except Exception as e:
                        st.error(f"❌ Terjadi kesalahan: {e}")
            else:
                st.warning("📸 Harap ambil foto terlebih dahulu!")

# --- 6. HALAMAN REKAP ---
else:
    st.markdown('<p class="hero-title">📊 Rekap Absensi Bulanan</p>', unsafe_allow_html=True)
    
    list_bulan = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    col1, col2 = st.columns(2)
    with col1:
        pilih_bulan = st.selectbox("Pilih Bulan:", list_bulan, index=waktu_aktif.month - 1)
    with col2:
        pilih_tahun = st.selectbox("Pilih Tahun:", [2025, 2026, 2027], index=1)

    if st.button("🔍 Tampilkan Data Rekap", use_container_width=True):
        with st.spinner("Mengambil data..."):
            try:
                target_query = f"{pilih_bulan} {pilih_tahun}"
                res = requests.get(f"{WEBAPP_URL}?bulan={target_query}", timeout=20).json()
                
                if res and len(res) > 0:
                    df = pd.DataFrame(res)
                    # Jika kolom Foto ada, tampilkan sebagai link/image jika diinginkan, 
                    # namun untuk saat ini kita tampilkan tabel teks saja.
                    st.table(df)
                else:
                    st.warning(f"ℹ️ Belum ada data absensi untuk periode {target_query}.")
            except Exception as e:
                st.error("❌ Gagal terhubung ke server. Pastikan URL Web App sudah benar dan berstatus 'Anyone'.")
