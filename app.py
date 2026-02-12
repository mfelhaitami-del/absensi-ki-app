import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image
import io
import numpy as np

# --- KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
# TEMPEL URL BARU DI SINI
WEBAPP_URL = "https://script.google.com/macros/s/AKfycby9FxDmJMGJreA0grhfz6W8Fr8uY2FRpn9S8-wpilZ5faeW7ErrSYr2Y4r6ekDOwPts/exec"

st.set_page_config(page_title="Absensi KI", layout="wide")

# Sidebar
with st.sidebar:
    st.header("MENU")
    menu = st.selectbox("Pilih:", ["📍 Absensi", "📊 Rekap"])
    w_wib = datetime.datetime.now() + datetime.timedelta(hours=7)
    st.write(f"Jam: {w_wib.strftime('%H:%M:%S')} WIB")

# Logika Halaman
if menu == "📍 Absensi":
    st.title("Absensi Tim KI")
    status = "MASUK" if 6 <= w_wib.hour < 12 else "PULANG" if 12 <= w_wib.hour < 23 else "TUTUP"
    
    if status == "TUTUP":
        st.error("Sesi Tutup")
    else:
        nama = st.selectbox("Nama:", ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"])
        foto = st.camera_input("Foto")
        if st.button("KIRIM") and foto:
            # Upload & Kirim
            res_img = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": foto.getvalue()}).json()
            link = res_img["data"]["url"]
            payload = {"nama": nama, "tanggal": w_wib.strftime("%Y-%m-%d"), "jam": w_wib.strftime("%H:%M:%S"), "status": status, "foto_link": link}
            requests.post(WEBAPP_URL, json=payload)
            st.success("Terkirim!")

else:
    st.title("📊 Rekap Data")
    list_b = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    c1, c2 = st.columns(2)
    bln = c1.selectbox("Bulan:", list_b, index=w_wib.month - 1)
    thn = c2.selectbox("Tahun:", [2025, 2026, 2027], index=1)

    if st.button("🔍 Tampilkan Rekap"):
        try:
            # Menggunakan URL Deployment baru
            response = requests.get(f"{WEBAPP_URL}?bulan={bln} {thn}", timeout=20)
            data = response.json()
            if data:
                st.dataframe(pd.DataFrame(data), use_container_width=True)
            else:
                st.info("Data kosong.")
        except Exception as e:
            st.error(f"Server tidak merespon. Pastikan Deploy sudah 'Anyone'.")
