import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image
import io
import numpy as np

# --- 1. KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
# MASUKKAN URL HASIL DEPLOY ULANG TADI DI SINI
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzLcIzxARZMacmv2pFOEvtwef0GSxHYVT_z-fLLDZUXYqf8J81NuOXGRcSuHkmq9Exq/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# --- 2. CSS CUSTOM ---
st.markdown("""
<style>
    [data-testid="stCameraInput"] video, [data-testid="stCameraInput"] img { transform: scaleX(-1); }
    .stApp { background: #1a1a1a; color: white; }
    .sidebar-box { background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #3b82f6; }
</style>
""", unsafe_allow_html=True)

@st.fragment(run_every="1s")
def jam_wib():
    w = datetime.datetime.now() + datetime.timedelta(hours=7)
    st.markdown(f'<div class="sidebar-box"><b>{w.strftime("%d %B %Y")}</b><br><span style="font-size:24px; color:#3b82f6;">{w.strftime("%H:%M:%S")} WIB</span></div>', unsafe_allow_html=True)
    return w

with st.sidebar:
    st.header("🏢 MENU UTAMA")
    menu = st.selectbox("Layanan:", ["📍 Absensi", "📊 Rekap Absensi"])
    st.divider()
    w_aktif = jam_wib()

# --- HALAMAN ABSENSI ---
if menu == "📍 Absensi":
    st.title("Absensi Tim KI Satker PPS Banten")
    
    # Perbaikan NameError: Gunakan variabel yang konsisten
    if 6 <= w_aktif.hour < 12: status_sesi = "MASUK"
    elif 12 <= w_aktif.hour < 23: status_sesi = "PULANG"
    else: status_sesi = "TUTUP"
    
    if status_sesi == "TUTUP":
        st.warning("🚫 Sesi Absensi sedang ditutup.")
    else:
        nama = st.selectbox("Pilih Nama:", ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"])
        foto = st.camera_input("Ambil Foto Wajah")
        
        if st.button("KIRIM DATA ABSENSI", use_container_width=True):
            if foto:
                with st.spinner("Mengirim data..."):
                    try:
                        # Flip foto agar tidak mirror di database
                        img = Image.open(foto).convert("RGB")
                        f_img = Image.fromarray(np.flip(np.array(img), axis=1))
                        buf = io.BytesIO()
                        f_img.save(buf, format="JPEG")
                        
                        # Upload ImgBB
                        r_img = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": buf.getvalue()}).json()
                        link = r_img["data"]["url"]
                        
                        # Kirim GSheets
                        payload = {"nama": nama, "tanggal": w_aktif.strftime("%Y-%m-%d"), "jam": w_aktif.strftime("%H:%M:%S"), "status": status_sesi, "foto_link": link}
                        requests.post(WEBAPP_URL, json=payload, timeout=20)
                        
                        st.success("✅ Berhasil dikirim!")
                        
                    except Exception as e:
                        st.error(f"Gagal mengirim: {e}")
            else: st.warning("📸 Ambil foto terlebih dahulu!")

# --- HALAMAN REKAP ---
else:
    st.title("📊 Rekap Absensi Bulanan")
    list_b = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    c1, c2 = st.columns(2)
    bln = c1.selectbox("Pilih Bulan:", list_b, index=w_aktif.month - 1)
    thn = c2.selectbox("Pilih Tahun:", [2025, 2026, 2027], index=1)

    if st.button("🔍 Tampilkan Data Rekap", use_container_width=True):
        try:
            # Menggunakan timeout lebih lama untuk pengambilan data
            response = requests.get(f"{WEBAPP_URL}?bulan={bln} {thn}", timeout=30)
            data_json = response.json()
            
            if isinstance(data_json, list) and len(data_json) > 0:
                st.dataframe(pd.DataFrame(data_json), use_container_width=True)
            else:
                st.info(f"ℹ️ Belum ada data untuk {bln} {thn}.")
        except Exception as e:
            st.error(f"❌ Terjadi kesalahan saat mengambil data. Pastikan URL baru sudah di-deploy dengan benar.")
