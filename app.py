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

# Menggunakan waktu WIB
waktu_wib = datetime.datetime.now() + datetime.timedelta(hours=7)
st.title("📸 Absensi Foto Real-Time")

daftar_nama = ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"]

nama = st.selectbox("Pilih Nama Anda", daftar_nama)
foto = st.camera_input("Ambil Foto Wajah")

if st.button("Kirim Absen"):
    if foto:
        with st.spinner("Mengolah foto agar tidak mirror..."):
            try:
                # 1. Buka foto yang diambil
                img = Image.open(foto)
                
                # 2. PROSES PEMBALIKAN (Agar hasil jadi REAL / Non-Mirror)
                # Karena kamera depan aslinya mirror, kita balik secara horizontal
                img_real = ImageOps.mirror(img)
                
                # Simpan ke memori
                buf = BytesIO()
                img_real.save(buf, format="JPEG")
                byte_im = buf.getvalue()

                # 3. Upload ke ImgBB
                files = {"image": byte_im}
                resp = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files=files)
                link_foto = resp.json()["data"]["url"]

                # 4. Kirim ke Google Sheets
                data = {
                    "nama": nama,
                    "tanggal": waktu_wib.strftime("%Y-%m-%d"),
                    "jam": waktu_wib.strftime("%H:%M:%S"),
                    "foto_link": link_foto
                }
                
                requests.post(WEBAPP_URL, json=data)
                
                st.success(f"✅ Berhasil! Hasil foto sudah diproses agar tidak mirror.")
                
            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")
    else:
        st.warning("Ambil foto dulu!")
