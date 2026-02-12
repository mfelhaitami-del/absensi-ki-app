import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image
import io
import numpy as np

# --- 1. KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
# PASTI GANTI DENGAN URL BARU DARI LANGKAH DI ATAS
WEBAPP_URL = "https://script.google.com/macros/s/AKfycby9FxDmJMGJreA0grhfz6W8Fr8uY2FRpn9S8-wpilZ5faeW7ErrSYr2Y4r6ekDOwPts/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# --- 2. CSS CUSTOM (Fix Mirror Camera) ---
st.markdown("""
<style>
    [data-testid="stCameraInput"] video, [data-testid="stCameraInput"] img { transform: scaleX(-1); }
    .stApp { background-color: #0e1117; color: white; }
    .sidebar-time { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #3b82f6; }
</style>
""", unsafe_allow_html=True)

@st.fragment(run_every="1s")
def jam_wib():
    w = datetime.datetime.now() + datetime.timedelta(hours=7)
    st.markdown(f'<div class="sidebar-time"><b>{w.strftime("%d %B %Y")}</b><br><span style="font-size:22px; color:#3b82f6;">{w.strftime("%H:%M:%S")} WIB</span></div>', unsafe_allow_html=True)
    return w

with st.sidebar:
    st.header("🏢 MENU UTAMA")
    menu = st.selectbox("Pilih Layanan:", ["📍 Absensi", "📊 Rekap Absensi"])
    st.divider()
    w_aktif = jam_wib()

# --- HALAMAN ABSENSI ---
if menu == "📍 Absensi":
    st.title("Absensi Tim KI Satker PPS Banten")
    
    # Penentuan Sesi
    if 6 <= w_aktif.hour < 12: status_sesi = "MASUK"
    elif 12 <= w_aktif.hour < 23: status_sesi = "PULANG"
    else: status_sesi = "TUTUP"
    
    if status_sesi == "TUTUP":
        st.error("🚫 Sesi Absensi sedang ditutup.")
    else:
        st.info(f"Sesi Sekarang: **Absen {status_sesi}**")
        nama = st.selectbox("Pilih Nama:", ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"])
        foto = st.camera_input("Ambil Foto Wajah")
        
        if st.button("KIRIM DATA ABSENSI", use_container_width=True):
            if foto:
                with st.spinner("Sedang memproses..."):
                    try:
                        # Balik foto agar tidak mirror di database
                        img = Image.open(foto).convert("RGB")
                        f_img = Image.fromarray(np.flip(np.array(img), axis=1))
                        buf = io.BytesIO()
                        f_img.save(buf, format="JPEG")
                        
                        # Upload ke ImgBB
                        r_img = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": buf.getvalue()}).json()
                        link = r_img["data"]["url"]
                        
                        # Kirim ke GSheets
                        payload = {"nama": nama, "tanggal": w_aktif.strftime("%Y-%m-%d"), "jam": w_aktif.strftime("%H:%M:%S"), "status": status_sesi, "foto_link": link}
                        requests.post(WEBAPP_URL, json=payload, timeout=20)
                        
                        st.success("✅ Absensi Berhasil Terkirim!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Gagal kirim data: {e}")
            else: st.warning("📸 Silakan ambil foto terlebih dahulu!")

# --- HALAMAN REKAP ---
else:
    st.title("📊 Rekap Absensi Bulanan")
    list_b = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    c1, c2 = st.columns(2)
    bln = c1.selectbox("Pilih Bulan:", list_b, index=w_aktif.month - 1)
    thn = c2.selectbox("Pilih Tahun:", [2025, 2026, 2027], index=1)

    if st.button("🔍 Tampilkan Data Rekap", use_container_width=True):
        try:
            # Request ke Web App
            query_url = f"{WEBAPP_URL}?bulan={bln} {thn}"
            response = requests.get(query_url, timeout=30)
            data_json = response.json()
            
            if data_json:
                df = pd.DataFrame(data_json)
                st.table(df) # Gunakan table agar lebih rapi
            else:
                st.info(f"Data untuk {bln} {thn} belum tersedia.")
        except Exception as e:
            st.error(f"Terjadi kesalahan saat mengambil data. Pastikan URL baru sudah di-deploy dengan benar. (Detail: {e})")
