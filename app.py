import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image, ImageDraw, ImageFont
import io
import numpy as np
import time
from streamlit_js_eval import get_geolocation

# --- KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
# GANTI DENGAN URL EXEC GOOGLE APPS SCRIPT ANDA
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbyJoDYYqRrxha8RG-ujACwPO8X68HgHZ1mkZr4ZPntFOu0w2Du12UyU5LP8Htb21EE/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# CSS: Perbaikan Mirror Kamera & Tampilan
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

# Fungsi Watermark dengan Lokasi & Teks Besar
def process_watermark(foto, nama, lat, lon, w_skrg):
    img = Image.open(foto).convert("RGB")
    # Anti-mirror: Membalikkan gambar agar hasil foto sesuai aslinya
    img = Image.fromarray(np.flip(np.array(img), axis=1))
    draw = ImageDraw.Draw(img)
    
    # Text info: Lokasi, Nama, Waktu (Status Dihapus)
    txt = f"NAMA: {nama}\nWAKTU: {w_skrg.strftime('%d/%m/%Y %H:%M:%S')}\nLOKASI: {lat}, {lon}"
    
    # Pengaturan ukuran teks otomatis berdasarkan lebar foto
    try:
        font_size = int(img.width * 0.035) # Ukuran dinamis
        font = ImageFont.load_default(size=font_size)
    except:
        font = ImageFont.load_default()
    
    # Posisi teks di pojok kiri bawah (agak ke atas sedikit)
    pos = (30, img.height - (img.height // 5))
    
    # Tambah bayangan teks hitam agar terbaca jelas
    draw.multiline_text((pos[0]+2, pos[1]+2), txt, fill=(0, 0, 0), font=font, spacing=10)
    draw.multiline_text(pos, txt, fill=(255, 255, 255), font=font, spacing=10)
    
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def kirim_data(nama, status, foto_bytes, koordinat, w_skrg):
    try:
        # Upload Foto ke ImgBB
        r_img = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": foto_bytes}).json()
        link = r_img["data"]["url"]
        
        # Kirim Data ke Google Sheets
        payload = {
            "nama": nama, "tanggal": w_skrg.strftime("%Y-%m-%d"), 
            "jam": w_skrg.strftime("%H:%M:%S"), "status": status, 
            "foto_link": link, "lokasi": koordinat
        }
        requests.post(WEBAPP_URL, json=payload, timeout=25)
        return True
    except:
        return False

# --- UI UTAMA ---
with st.sidebar:
    st.header("🏢 MENU UTAMA")
    menu = st.selectbox("Layanan:", ["📍 Absensi", "📊 Rekap Absensi"])
    st.divider()
    w_skrg = datetime.datetime.now() + datetime.timedelta(hours=7)
    st.markdown(f'''<div class="sidebar-box"><b>{w_skrg.strftime("%d %B %Y")}</b><br>
    <span style="font-size:20px; color:#3b82f6;">{w_skrg.strftime("%H:%M:%S")} WIB</span></div>''', unsafe_allow_html=True)

if menu == "📍 Absensi":
    st.markdown("<h2 style='text-align:center; color:white;'>Absensi Tim KI Satker PPS Banten</h2>", unsafe_allow_html=True)
    
    # AMBIL GPS (Browser akan meminta izin)
    loc = get_geolocation()
    
    sesi = "MASUK" if 6 <= w_skrg.hour < 12 else "PULANG" if 12 <= w_skrg.hour < 23 else "TUTUP"
    
    if sesi == "TUTUP":
        st.error("🚫 Sesi absensi sudah ditutup hari ini.")
    else:
        nama = st.selectbox("Pilih Nama Anda:", ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"])
        foto = st.camera_input("Ambil Foto Wajah")
        
        if st.button("KIRIM ABSEN SEKARANG", use_container_width=True, type="primary"):
            if not loc:
                st.error("📍 Akses Lokasi (GPS) diperlukan! Mohon klik 'Allow/Izinkan' saat browser meminta lokasi.")
            elif foto:
                lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
                koordinat = f"{lat}, {lon}"
                
                with st.spinner("Sedang memproses foto dan lokasi..."):
                    foto_final = process_watermark(foto, nama, lat, lon, w_skrg)
                    if kirim_data(nama, sesi, foto_final, koordinat, w_skrg):
                        st.success(f"✅ Absen {sesi} Berhasil dikirim!")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("❌ Gagal mengirim ke server. Cek koneksi internet.")
            else:
                st.warning("📸 Silakan ambil foto terlebih dahulu!")

else:
    # Halaman Rekap Bulanan
    st.markdown("<h2 style='text-align:center; color:white;'>📊 Rekap Absensi</h2>", unsafe_allow_html=True)
    list_b = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    col1, col2 = st.columns(2)
    with col1:
        b = st.selectbox("Pilih Bulan:", list_b, index=w_skrg.month - 1)
    with col2:
        y = st.selectbox("Pilih Tahun:", [2025, 2026, 2027], index=1)
        
    if st.button("Tampilkan Data Rekap", use_container_width=True):
        try:
            res = requests.get(f"{WEBAPP_URL}?bulan={b} {y}", timeout=25).json()
            if res:
                df = pd.DataFrame(res)
                df.insert(0, 'No', range(1, 1 + len(df)))
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info(f"Belum ada data untuk bulan {b} {y}")
        except:
            st.error("Gagal terhubung ke database.")
