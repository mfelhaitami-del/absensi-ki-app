import streamlit as st
import pandas as pd
import datetime
import requests

# --- KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbziJDBwWIM6NAsi4ZqBcnOMkmhwrjCbCg5TzvguDmW5VvQnVj0OeyOOLr4u4j4sWRjl/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="centered")

waktu_wib = datetime.datetime.now() + datetime.timedelta(hours=7)
st.title("📸 Absensi Foto Real-Time")

daftar_nama = ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"]

nama = st.selectbox("Pilih Nama", daftar_nama)
foto = st.camera_input("Ambil Foto Wajah")

if st.button("Kirim Absen"):
    if foto:
        with st.spinner("Mengirim ke Google Sheets..."):
            # 1. Upload ke ImgBB
            files = {"image": foto.getvalue()}
            resp = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files=files)
            link_foto = resp.json()["data"]["url"]

            # 2. Kirim ke Google Sheets lewat Web App
            data = {
                "nama": nama,
                "tanggal": waktu_wib.strftime("%Y-%m-%d"),
                "jam": waktu_wib.strftime("%H:%M:%S"),
                "foto_link": link_foto
            }
            
            # Kirim data tanpa library ribet
            requests.post(WEBAPP_URL, json=data)
            st.success(f"✅ Berhasil! Data {nama} sudah masuk ke Sheets.")
    else:
        st.warning("Ambil foto dulu!")
