import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image, ImageOps
from io import BytesIO

# --- KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbziJDBwWIM6NAsi4ZqBcnOMkmhwrjCbCg5TzvguDmW5VvQnVj0OeyOOLr4u4j4sWRjl/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="centered")

# --- CSS UNTUK KAMERA REAL (TIDAK MIRROR) ---
st.markdown("""
    <style>
    /* Mengakses elemen video kamera dan mematikannya efek mirror-nya */
    video {
        -webkit-transform: scaleX(1) !important;
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
        with st.spinner("Memproses foto & mengirim data..."):
            try:
                # Kita ambil foto apa adanya (tanpa proses mirror lagi di kode)
                img = Image.open(foto)
                
                # Simpan ke memori untuk diupload
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
                
                # Menampilkan pesan sukses saja tanpa st.balloons()
                st.success(f"✅ Berhasil! Absensi {nama} telah tersimpan.")
                
            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")
    else:
        st.warning("Ambil foto dulu!")
