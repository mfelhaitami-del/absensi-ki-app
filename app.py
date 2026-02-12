import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image
import io
import numpy as np

# --- KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
# GANTI DENGAN URL /exec HASIL NEW DEPLOYMENT ANDA
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbw1b4y97wTIZTLEiY7lSvJ2osMuHWH3k6XTnoFPwZGOMKTjBgqdocFgAS2Y0CdEaEYN/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# CSS Background & No-Mirror Camera
st.markdown("""
    <style>
    [data-testid="stCameraInput"] video, [data-testid="stCameraInput"] img { transform: scaleX(-1); }
    .stApp {
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
        url("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Logo_PU_%28RGB%29.jpg/960px-Logo_PU_%28RGB%29.jpg");
        background-size: cover; background-attachment: fixed;
    }
    </style>
""", unsafe_allow_html=True)

# Jam WIB Real-time
@st.fragment(run_every="1s")
def jam_sidebar():
    w = datetime.datetime.now() + datetime.timedelta(hours=7)
    st.sidebar.markdown(f"### ⏰ {w.strftime('%H:%M:%S')} WIB")
    return w

with st.sidebar:
    st.header("🏢 MENU")
    menu = st.selectbox("Pilih Layanan:", ["📍 Absensi", "📊 Rekap Data"])
    w_skrg = jam_sidebar()

if menu == "📍 Absensi":
    st.title("📍 Absensi Tim KI")
    status_sesi = "MASUK" if 6 <= w_skrg.hour < 12 else "PULANG" if 12 <= w_skrg.hour < 23 else "TUTUP"
    
    nama = st.selectbox("Nama:", ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"])
    foto = st.camera_input("Ambil Foto")
    
    if st.button("KIRIM ABSENSI", use_container_width=True):
        if foto:
            with st.spinner("Mengirim..."):
                try:
                    # Proses Gambar
                    img = Image.open(foto).convert("RGB")
                    f_img = Image.fromarray(np.flip(np.array(img), axis=1))
                    buf = io.BytesIO()
                    f_img.save(buf, format="JPEG")
                    
                    # Upload Foto
                    r_img = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": buf.getvalue()}).json()
                    link = r_img["data"]["url"]
                    
                    # Kirim Data
                    payload = {"nama": nama, "tanggal": w_skrg.strftime("%Y-%m-%d"), "jam": w_skrg.strftime("%H:%M:%S"), "status": status_sesi, "foto_link": link}
                    requests.post(WEBAPP_URL, json=payload)
                    st.success(f"✅ Berhasil absen {status_sesi}!")
                except:
                    st.error("❌ Terjadi kesalahan koneksi.")
        else: st.warning("📸 Foto wajib diambil!")

else:
    st.title("📊 Rekap Data Absensi")
    # LIST BULAN INDONESIA (Penting agar sinkron dengan Nama Tab)
    list_b = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    c1, c2 = st.columns(2)
    b = c1.selectbox("Bulan:", list_b, index=w_skrg.month - 1)
    t = c2.selectbox("Tahun:", [2025, 2026, 2027], index=1)

    if st.button("🔍 Tampilkan Rekap", use_container_width=True):
        try:
            # Mengirim request bulan dalam bahasa Indonesia (e.g. "Februari 2026")
            res = requests.get(f"{WEBAPP_URL}?bulan={b} {t}").json()
            if res:
                df = pd.DataFrame(res)
                df.insert(0, 'No', range(1, 1 + len(df)))
                st.table(df) # Gunakan st.table agar format teks murni terjaga
            else:
                st.info(f"Belum ada data di tab '{b} {t}'.")
        except:
            st.error("Gagal mengambil data. Pastikan URL Deployment sudah benar.")
