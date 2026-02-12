import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image
import io
import numpy as np

# --- 1. KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
# GANTI URL DI BAWAH INI DENGAN URL BARU HASIL DEPLOY ULANG
WEBAPP_URL = "ISI_DENGAN_URL_WEB_APP_BARU_ANDA"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# --- 2. CSS CUSTOM ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
    [data-testid="stCameraInput"] video, [data-testid="stCameraInput"] img { transform: scaleX(-1); }
    .stApp {
        background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), 
        url("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Logo_PU_%28RGB%29.jpg/960px-Logo_PU_%28RGB%29.jpg");
        background-size: cover; background-position: center; background-attachment: fixed;
    }
    .sidebar-time { background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #3b82f6; }
    </style>
""", unsafe_allow_html=True)

@st.fragment(run_every="1s")
def jam_sidebar():
    w = datetime.datetime.now() + datetime.timedelta(hours=7)
    st.markdown(f'<div class="sidebar-time"><span style="color:white">{w.strftime("%d %B %Y")}</span><br><span style="font-size:24px; color:#3b82f6; font-weight:bold;">{w.strftime("%H:%M:%S")}</span><br><small style="color:white">WIB</small></div>', unsafe_allow_html=True)
    return w

with st.sidebar:
    st.header("🏢 MENU UTAMA")
    menu = st.selectbox("Layanan:", ["📍 Absensi", "📊 Rekap Absensi"])
    st.divider()
    waktu_skrg = jam_sidebar()

if menu == "📍 Absensi":
    st.markdown("<h2 style='text-align:center; color:white;'>Absensi Tim KI Satker PPS Banten</h2>", unsafe_allow_html=True)
    sesi = "MASUK" if 6 <= waktu_skrg.hour < 12 else "PULANG" if 12 <= waktu_skrg.hour < 23 else "TUTUP"
    
    if sesi == "TUTUP":
        st.error("🚫 Sesi Absensi sedang ditutup.")
    else:
        nama = st.selectbox("Pilih Nama:", ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"])
        foto = st.camera_input("Ambil Foto Wajah")
        
        if st.button("KIRIM DATA ABSENSI", use_container_width=True):
            if foto:
                with st.spinner("Mengirim..."):
                    try:
                        img = Image.open(foto).convert("RGB")
                        f_img = Image.fromarray(np.flip(np.array(img), axis=1))
                        buf = io.BytesIO()
                        f_img.save(buf, format="JPEG")
                        
                        r_img = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": buf.getvalue()}).json()
                        
                        payload = {"nama": nama, "tanggal": waktu_skrg.strftime("%Y-%m-%d"), "jam": waktu_skrg.strftime("%H:%M:%S"), "status": sesi, "foto_link": r_img["data"]["url"]}
                        requests.post(WEBAPP_URL, json=payload, timeout=20)
                        st.success("✅ Berhasil dikirim!")
                        st.balloons()
                    except:
                        st.error("Gagal mengirim data.")
            else: st.warning("📸 Ambil foto dulu!")

else:
    st.markdown("<h2 style='text-align:center; color:white;'>📊 Rekap Absensi Bulanan</h2>", unsafe_allow_html=True)
    list_b = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    c1, c2 = st.columns(2)
    b = c1.selectbox("Bulan:", list_b, index=waktu_skrg.month - 1)
    t = c2.selectbox("Tahun:", [2025, 2026, 2027], index=1)

    if st.button("🔍 Tampilkan Data Rekap", use_container_width=True):
        try:
            # Gunakan timeout yang lebih lama untuk Google Sheets
            response = requests.get(f"{WEBAPP_URL}?bulan={b} {t}", timeout=30)
            res = response.json()
            
            if res and len(res) > 0:
                df = pd.DataFrame(res)
                st.dataframe(df, use_container_width=True)
            else:
                st.info(f"Data {b} {t} belum tersedia.")
        except Exception as e:
            st.error(f"Koneksi terputus atau server lambat. Pastikan URL Deployment sudah benar dan diset ke 'Anyone'.")
