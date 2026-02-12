import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image, ImageDraw, ImageFont
import io
import numpy as np
import time
import streamlit.components.v1 as components

# --- KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
# Pastikan URL Web App Google Script Anda sudah benar di bawah ini
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbyJoDYYqRrxha8RG-ujACwPO8X68HgHZ1mkZr4ZPntFOu0w2Du12UyU5LP8Htb21EE/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# CSS: Styling UI & Kamera
st.markdown("""
    <style>
    [data-testid="stCameraInput"] video { transform: scaleX(-1); }
    [data-testid="stCameraInput"] img { transform: scaleX(-1); }
    .stApp {
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
        url("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Logo_PU_%28RGB%29.jpg/960px-Logo_PU_%28RGB%29.jpg");
        background-size: cover; background-attachment: fixed;
    }
    .sidebar-box { background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #3b82f6; color: white; }
    </style>
""", unsafe_allow_html=True)

# --- JALUR PINTAS GPS (JavaScript) ---
def get_location_js():
    js_code = """
    <script>
    navigator.geolocation.getCurrentPosition(
        (position) => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            window.parent.postMessage({
                type: 'streamlit:setComponentValue',
                value: {lat: lat, lon: lon}
            }, '*');
        },
        (error) => {
            window.parent.postMessage({
                type: 'streamlit:setComponentValue',
                value: {error: error.message}
            }, '*');
        }
    );
    </script>
    """
    return components.html(js_code, height=0)

# --- FUNGSI WATERMARK ---
def process_watermark(foto, nama, lat, lon, w_skrg):
    img = Image.open(foto).convert("RGB")
    img = Image.fromarray(np.flip(np.array(img), axis=1)) # Fix mirror kamera
    draw = ImageDraw.Draw(img)
    
    # Teks Info: Nama, Waktu, Lokasi (Status Terverifikasi Dihapus)
    txt = f"NAMA: {nama}\nWAKTU: {w_skrg.strftime('%d/%m/%Y %H:%M:%S')}\nLOKASI: {lat}, {lon}"
    
    # Ukuran teks dinamis (besar)
    f_size = int(img.width * 0.045)
    try:
        font = ImageFont.load_default(size=f_size)
    except:
        font = ImageFont.load_default()
    
    # Posisi di kiri bawah
    pos = (40, img.height - (img.height // 4))
    
    # Bayangan teks (Shadow)
    draw.multiline_text((pos[0]+2, pos[1]+2), txt, fill=(0, 0, 0), font=font, spacing=8)
    # Teks Utama (Putih)
    draw.multiline_text(pos, txt, fill=(255, 255, 255), font=font, spacing=8)
    
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

# --- FUNGSI KIRIM DATA ---
def kirim_data(nama, status, foto_bytes, koordinat, w_skrg):
    try:
        # 1. Upload ke ImgBB
        r_img = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": foto_bytes}).json()
        link = r_img["data"]["url"]
        
        # 2. Kirim ke Google Sheets
        payload = {
            "nama": nama, "tanggal": w_skrg.strftime("%Y-%m-%d"), 
            "jam": w_skrg.strftime("%H:%M:%S"), "status": status, 
            "foto_link": link, "lokasi": koordinat
        }
        requests.post(WEBAPP_URL, json=payload, timeout=25)
        return True
    except:
        return False

# --- SIDEBAR & MENU ---
with st.sidebar:
    st.header("🏢 MENU UTAMA")
    menu = st.selectbox("Pilih Layanan:", ["📍 Absensi", "📊 Rekap Absensi"])
    st.divider()
    w_skrg = datetime.datetime.now() + datetime.timedelta(hours=7) # WIB
    st.markdown(f'''<div class="sidebar-box"><b>{w_skrg.strftime("%d %B %Y")}</b><br>
    <span style="font-size:20px; color:#3b82f6;">{w_skrg.strftime("%H:%M:%S")} WIB</span></div>''', unsafe_allow_html=True)

# --- HALAMAN ABSENSI ---
if menu == "📍 Absensi":
    st.markdown("<h2 style='text-align:center; color:white;'>Absensi Tim KI</h2>", unsafe_allow_html=True)
    
    # Ambil Lokasi JS
    loc_val = get_location_js()
    
    sesi = "MASUK" if 6 <= w_skrg.hour < 12 else "PULANG" if 12 <= w_skrg.hour < 23 else "TUTUP"
    
    if sesi == "TUTUP":
        st.error("🚫 Sesi Absensi sedang ditutup.")
    else:
        nama = st.selectbox("Pilih Nama:", ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"])
        foto = st.camera_input("Ambil Foto Wajah")
        
        if st.button("KIRIM ABSENSI SEKARANG", use_container_width=True, type="primary"):
            if not loc_val:
                st.warning("📍 Tunggu sebentar sedang mendeteksi lokasi... Pastikan GPS HP aktif!")
            elif foto:
                # Koordinat dari JS Component
                try:
                    lat = loc_val.get('lat', '-6.12')
                    lon = loc_val.get('lon', '106.15')
                except:
                    lat, lon = "-6.12", "106.15" # Fallback Serang
                
                koordinat = f"{lat}, {lon}"
                
                with st.spinner("Sedang memproses dan mengirim data..."):
                    foto_final = process_watermark(foto, nama, lat, lon, w_skrg)
                    if kirim_data(nama, sesi, foto_final, koordinat, w_skrg):
                        st.success(f"✅ Berhasil! Selamat {sesi.lower()}, {nama}.")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("❌ Gagal mengirim ke server. Cek koneksi.")
            else:
                st.warning("📸 Silakan ambil foto terlebih dahulu!")

# --- HALAMAN REKAP ABSENSI ---
else:
    st.markdown("<h2 style='text-align:center; color:white;'>📊 Rekap Absensi Bulanan</h2>", unsafe_allow_html=True)
    
    list_bulan = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    
    col1, col2 = st.columns(2)
    with col1:
        b = st.selectbox("Pilih Bulan:", list_bulan, index=w_skrg.month - 1)
    with col2:
        y = st.selectbox("Pilih Tahun:", [2025, 2026, 2027], index=1)
        
    if st.button("🔍 Tampilkan Data Rekap", use_container_width=True):
        try:
            with st.spinner(f"Mengambil data rekap {b} {y}..."):
                # Query ke Google Script
                res = requests.get(f"{WEBAPP_URL}?bulan={b} {y}", timeout=25).json()
            
            if res and len(res) > 0:
                df = pd.DataFrame(res)
                df.insert(0, 'No', range(1, 1 + len(df)))
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info(f"ℹ️ Belum ada data absensi untuk periode {b} {y}.")
        except:
            st.error("❌ Gagal mengambil data. Pastikan nama Sheet di Google Spreadsheet sesuai (Contoh: 'Februari 2026').")
