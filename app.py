import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import numpy as np
import time

# --- KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
# GANTI URL DI BAWAH DENGAN URL WEB APP GOOGLE SCRIPT ANDA YANG BARU
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxuH6AdWUeMkWagwsnYqhWO8_d_sgN0TO2TSBilPb7uiCFvx3MqoquFpx6TdAVmeLGV/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# CSS: Styling & Fix Camera Mirror
st.markdown("""
    <style>
    [data-testid="stCameraInput"] video { transform: scaleX(-1); border-radius: 10px; border: 3px solid #3b82f6; }
    .stApp { background: #0e1117; color: white; }
    .sidebar-box { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; border: 1px solid #3b82f6; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI WATERMARK & KIRIM ---
def proses_dan_kirim(nama, status, foto_raw, waktu):
    try:
        # 1. Olah Foto
        img = Image.open(foto_raw).convert("RGB")
        img = ImageOps.mirror(img) # Balik agar teks tidak terbalik
        
        # 2. Gambar Watermark
        draw = ImageDraw.Draw(img)
        tgl_str = waktu.strftime("%A, %d %b %Y").replace("Monday","Senin").replace("Tuesday","Selasa").replace("Wednesday","Rabu").replace("Thursday","Kamis").replace("Friday","Jumat").replace("Saturday","Sabtu").replace("Sunday","Minggu")
        jam_str = waktu.strftime("%H:%M:%S") + " WIB"
        
        # Teks yang akan ditempel
        teks_watermark = f"NAMA: {nama}\nWAKTU: {tgl_str}\nJAM: {jam_str}\nSTATUS: {status}"
        
        # Gunakan font bawaan (size disesuaikan dengan lebar gambar)
        font_size = int(img.width * 0.04)
        try:
            font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()

        # Posisi di kiri bawah
        posisi = (20, img.height - (font_size * 5))
        
        # Gambar Bayangan (Hitam) agar teks terbaca
        draw.multiline_text((posisi[0]+2, posisi[1]+2), teks_watermark, fill="black", font=font, spacing=5)
        # Gambar Teks Utama (Putih)
        draw.multiline_text(posisi, teks_watermark, fill="white", font=font, spacing=5)

        # 3. Simpan ke Buffer
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        
        # 4. Upload ImgBB
        file_foto = {"image": buf.getvalue()}
        res_img = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files=file_foto).json()
        url_foto = res_img["data"]["url"]

        # 5. Kirim ke Google Sheets
        payload = {
            "nama": nama,
            "tanggal": waktu.strftime("%Y-%m-%d"),
            "jam": waktu.strftime("%H:%M:%S"),
            "status": status,
            "foto_link": url_foto
        }
        r = requests.post(WEBAPP_URL, json=payload, timeout=15)
        return r.status_code == 200
    except Exception as e:
        st.error(f"Error Detail: {e}")
        return False

# --- UI APP ---
with st.sidebar:
    st.header("MENU")
    menu = st.selectbox("Pilih Layanan:", ["📍 Presensi", "📊 Rekap"])
    st.divider()
    # Jam Digital Sidebar
    w_skrg = datetime.datetime.now() + datetime.timedelta(hours=7)
    st.markdown(f"""<div class='sidebar-box'>
        <div style='font-size:12px;'>{w_skrg.strftime('%d %B %Y')}</div>
        <div style='font-size:22px; font-weight:bold; color:#3b82f6;'>{w_skrg.strftime('%H:%M:%S')} WIB</div>
    </div>""", unsafe_allow_html=True)

if menu == "📍 Presensi":
    st.title("Presensi Tim KI")
    
    nama = st.selectbox("Pilih Nama:", ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"])
    
    # Sesi Otomatis
    sesi = "MASUK" if w_skrg.hour < 12 else "PULANG"
    st.info(f"Sesi Aktif: **{sesi}**")
    
    foto = st.camera_input("Ambil Foto")
    
    if st.button("KIRIM ABSENSI SEKARANG", type="primary", use_container_width=True):
        if foto is not None:
            with st.spinner("Sedang memproses foto & mengirim data..."):
                sukses = proses_dan_kirim(nama, sesi, foto, w_skrg)
                if sukses:
                    st.success(f"Berhasil! Absensi {nama} telah tercatat.")
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Gagal mengirim. Periksa koneksi atau URL Apps Script Anda.")
        else:
            st.warning("Silakan ambil foto terlebih dahulu!")

else:
    st.title("Rekap Absensi")
    st.write("Data dapat dilihat langsung di Google Sheets Anda.")
