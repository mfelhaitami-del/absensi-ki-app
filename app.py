import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image
import io
import numpy as np

# --- 1. KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbw3AtbN2Znxq1XJDEYHkgQqC-G8SU_7RcwptjmzzS9dXNyd5iK8d-Kk3cKaODfl_FrC/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# --- 2. CUSTOM CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }

    /* Preview LIVE kamera agar mirror (nyaman saat berpose) */
    [data-testid="stCameraInput"] video {
        transform: scaleX(-1) !important;
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
        font-size: 32px; font-weight: 800; text-align: center; 
        color: #ffffff; margin-top: -30px; margin-bottom: 30px;
        text-shadow: 2px 4px 8px rgba(0,0,0,0.8);
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNGSI JAM WIB ---
@st.fragment(run_every="1s")
def jam_sidebar():
    waktu_skrg = datetime.datetime.now() + datetime.timedelta(hours=7)
    st.markdown(f"""
    <div class="sidebar-time-box">
        <span style="font-size: 14px;">{waktu_skrg.strftime('%d %B %Y')}</span><br>
        <span style="font-size: 28px; color: #3b82f6; font-weight: bold;">{waktu_skrg.strftime('%H:%M:%S')}</span><br>
        <b>WIB</b>
    </div>
    """, unsafe_allow_html=True)
    return waktu_skrg

# --- 4. NAVIGASI ---
with st.sidebar:
    st.markdown("### 🏢 MENU UTAMA")
    menu = st.selectbox("Pilih Layanan:", ["📍 Absensi", "📊 Rekap Absensi"])
    st.divider()
    waktu_aktif = jam_sidebar()

# --- 5. HALAMAN ABSENSI ---
if menu == "📍 Absensi":
    st.markdown('<p class="hero-title">Absensi Tim KI Satker PPS Banten</p>', unsafe_allow_html=True)
    
    status_sesi = "TUTUP"
    if 6 <= waktu_aktif.hour < 12: status_sesi = "MASUK"
    elif 12 <= waktu_aktif.hour < 23: status_sesi = "PULANG"
    
    if status_sesi == "TUTUP":
        st.error(f"🚫 Sesi Absensi Tutup.")
    else:
        nama = st.selectbox("Pilih Nama:", ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"])
        
        # Bagian Ambil Foto (Hanya kamera saja tanpa pratinjau tambahan di bawahnya)
        foto_raw = st.camera_input("Ambil Foto Wajah (Pastikan Terang)")
        
        if st.button("KIRIM DATA ABSENSI", use_container_width=True):
            if foto_raw:
                with st.spinner("Mengirim data..."):
                    try:
                        # --- LOGIKA PEMBALIKAN DI LATAR BELAKANG ---
                        img = Image.open(foto_raw).convert("RGB")
                        img_array = np.array(img)
                        # Membalikkan pixel secara horizontal agar tidak mirror
                        flipped_array = np.flip(img_array, axis=1) 
                        img_final = Image.fromarray(flipped_array)

                        # Simpan ke byte stream untuk diunggah
                        buf = io.BytesIO()
                        img_final.save(buf, format="JPEG", quality=95)
                        final_bytes = buf.getvalue()

                        # 1. Upload ke ImgBB
                        res_img = requests.post(
                            f"https://api.imgbb.com/1/upload?key={API_IMGBB}", 
                            files={"image": ("absensi.jpg", final_bytes, "image/jpeg")}
                        ).json()
                        link_foto = res_img["data"]["url"]
                        
                        # 2. Kirim ke Google Sheets
                        payload = {
                            "nama": nama, "tanggal": waktu_aktif.strftime("%Y-%m-%d"), 
                            "jam": waktu_aktif.strftime("%H:%M:%S"), "status": status_sesi, "foto_link": link_foto
                        }
                        requests.post(WEBAPP_URL, json=payload, timeout=20)
                        
                        st.success(f"✅ Berhasil Terkirim!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"⚠️ Terjadi kesalahan: {e}")
            else:
                st.warning("📸 Silakan ambil foto terlebih dahulu!")

# --- 6. HALAMAN REKAP ---
else:
    st.markdown('<p class="hero-title">📊 Rekap Absensi</p>', unsafe_allow_html=True)
    try:
        res = requests.get(f"{WEBAPP_URL}?bulan={waktu_aktif.strftime('%B %Y')}").json()
        if res:
            st.dataframe(pd.DataFrame(res)[["Nama", "Tanggal", "Jam Masuk", "Jam Pulang"]], use_container_width=True)
    except:
        st.error("Gagal memuat data.")
