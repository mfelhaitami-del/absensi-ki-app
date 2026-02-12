import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image, ImageDraw, ImageFont
import io
import numpy as np
import time
from streamlit_geospatial import github_get_geolocation

# --- KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbx3tEh9mSuiK4viX-GZZzEPoonb1Oi_j9fVrdNqlHXE5NjEccoBlar0ej5jodm6xbbv/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# CSS: Perbaikan Mirror & UI
st.markdown("""
    <style>
    [data-testid="stCameraInput"] video { transform: scaleX(-1); }
    [data-testid="stCameraInput"] img { transform: scaleX(-1); }
    .stApp {
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
        url("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Logo_PU_%28RGB%29.jpg/960px-Logo_PU_%28RGB%29.jpg");
        background-size: cover; background-attachment: fixed;
    }
    </style>
""", unsafe_allow_html=True)

def process_watermark(foto, nama, lat, lon, w_skrg):
    img = Image.open(foto).convert("RGB")
    # Fix mirror
    img = Image.fromarray(np.flip(np.array(img), axis=1))
    draw = ImageDraw.Draw(img)
    
    # Text info - Tulisan status dihapus sesuai permintaan
    txt = f"NAMA: {nama}\nWAKTU: {w_skrg.strftime('%d/%m/%Y %H:%M:%S')}\nLOKASI: {lat}, {lon}"
    
    # Ukuran font lebih besar
    try:
        font_size = int(img.width * 0.04)
        font = ImageFont.load_default(size=font_size)
    except:
        font = ImageFont.load_default()
    
    # Posisi di kiri bawah
    pos = (40, img.height - (img.height // 4))
    
    # Shadow hitam agar terbaca
    draw.multiline_text((pos[0]+2, pos[1]+2), txt, fill=(0, 0, 0), font=font, spacing=10)
    # Teks utama putih
    draw.multiline_text(pos, txt, fill=(255, 255, 255), font=font, spacing=10)
    
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def kirim_data(nama, status, foto_bytes, koordinat, w_skrg):
    try:
        r_img = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": foto_bytes}).json()
        link = r_img["data"]["url"]
        payload = {
            "nama": nama, "tanggal": w_skrg.strftime("%Y-%m-%d"), 
            "jam": w_skrg.strftime("%H:%M:%S"), "status": status, 
            "foto_link": link, "lokasi": koordinat
        }
        requests.post(WEBAPP_URL, json=payload, timeout=25)
        return True
    except: return False

# --- LOGIC UTAMA ---
with st.sidebar:
    st.header("🏢 MENU")
    menu = st.selectbox("Layanan:", ["📍 Absensi", "📊 Rekap"])
    w_skrg = datetime.datetime.now() + datetime.timedelta(hours=7)

if menu == "📍 Absensi":
    st.markdown("<h2 style='text-align:center; color:white;'>Absensi Tim KI</h2>", unsafe_allow_html=True)
    
    # Tombol GPS Manual (Lebih aman dari error loading otomatis)
    loc = github_get_geolocation()
    
    sesi = "MASUK" if 6 <= w_skrg.hour < 12 else "PULANG" if 12 <= w_skrg.hour < 23 else "TUTUP"
    
    if sesi == "TUTUP":
        st.error("🚫 Sesi Absensi ditutup.")
    else:
        nama = st.selectbox("Nama:", ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"])
        foto = st.camera_input("Ambil Foto")
        
        if st.button("KIRIM DATA", use_container_width=True, type="primary"):
            if not loc:
                st.warning("📍 Klik tombol 'Get Location' di atas dan izinkan akses GPS browser!")
            elif foto:
                lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
                koordinat = f"{lat}, {lon}"
                with st.spinner("Memproses..."):
                    foto_final = process_watermark(foto, nama, lat, lon, w_skrg)
                    if kirim_data(nama, sesi, foto_final, koordinat, w_skrg):
                        st.success("✅ Berhasil dikirim!")
                        time.sleep(2)
                        st.rerun()
                    else: st.error("Gagal kirim.")
            else: st.warning("Foto kosong!")
else:
    # Bagian rekap tetap menggunakan pilihan tahun
    st.markdown("<h2 style='text-align:center; color:white;'>📊 Rekap Absensi</h2>", unsafe_allow_html=True)
    list_b = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    c1, c2 = st.columns(2)
    with c1: b = st.selectbox("Bulan:", list_b, index=w_skrg.month - 1)
    with c2: y = st.selectbox("Tahun:", [2025, 2026, 2027], index=1)
        
    if st.button("Tampilkan Data", use_container_width=True):
        try:
            res = requests.get(f"{WEBAPP_URL}?bulan={b} {y}", timeout=25).json()
            if res:
                df = pd.DataFrame(res)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else: st.info("Data kosong.")
        except: st.error("Gagal ambil data.")
