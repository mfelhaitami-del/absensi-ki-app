import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image
from io import BytesIO

# --- KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbziJDBwWIM6NAsi4ZqBcnOMkmhwrjCbCg5TzvguDmW5VvQnVj0OeyOOLr4u4j4sWRjl/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="centered")

# --- CSS SAKTI UNTUK KAMERA REAL (ANTI-MIRROR) ---
st.markdown("""
    <style>
    /* Memaksa semua elemen video untuk tidak mirror */
    video {
        -webkit-transform: scaleX(1) !important;
        transform: scaleX(1) !important;
    }
    /* Tambahan untuk memastikan container juga tidak memutar balik */
    [data-testid="stCameraInput"] video {
        transform: scaleX(1) !important;
    }
    </style>
""", unsafe_allow_html=True)

waktu_wib = datetime.datetime.now() + datetime.timedelta(hours=7)
st.title("📸 Absensi Foto Real-Time")

daftar_nama = ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"]

nama = st.selectbox("Pilih Nama Anda", daftar_nama)
foto = st.camera_input("Ambil Foto Wajah")

if st.button("Kirim Absen"):
    if foto:
        with st.spinner("Mengirim data..."):
            try:
                # Ambil foto mentah (karena tampilan sudah real, hasil juga akan real)
                img = Image.open(foto)
                
                buf = BytesIO()
                img.save(buf, format="JPEG")
                byte_im = buf.getvalue()

                # 1. Upload ke ImgBB
                files = {"image": byte_im}
                resp = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files=files)
                link_foto = resp.json()["data"]["url"]

                # 2. Kirim ke Google Sheets lewat Web App
                data = {
                    "nama": nama,
                    "tanggal": waktu_wib.strftime("%Y-%m-%d"),
                    "jam": waktu_wib.strftime("%H:%M:%S"),
                    "foto_link": link_foto
                }
                
                requests.post(WEBAPP_URL, json=data)
                
                # Pesan sukses tanpa balon
                st.success(f"✅ Berhasil! Absensi {nama} tercatat.")
                
            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")
    else:
        st.warning("Ambil foto dulu!")
