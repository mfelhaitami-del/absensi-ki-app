import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image, ImageDraw, ImageFont
import io
import numpy as np
import time
import streamlit.components.v1 as components
from geopy.geocoders import Nominatim

# --- KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbyJoDYYqRrxha8RG-ujACwPO8X68HgHZ1mkZr4ZPntFOu0w2Du12UyU5LP8Htb21EE/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# CSS: Styling & Jam Real-time
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

# --- FUNGSI ALAMAT DETAIL ---
def get_address(lat, lon):
    try:
        geolocator = Nominatim(user_agent="absensi_ki_app")
        location = geolocator.reverse(f"{lat}, {lon}", timeout=10)
        return location.address if location else "Alamat tidak ditemukan"
    except:
        return "Gagal memuat alamat"

# --- JALUR PINTAS GPS ---
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
def process_watermark(foto, nama, lat, lon, alamat, w_skrg):
    img = Image.open(foto).convert("RGB")
    img = Image.fromarray(np.flip(np.array(img), axis=1)) # Fix mirror
    draw = ImageDraw.Draw(img)
    
    # Bungkus teks alamat agar tidak terlalu panjang ke samping
    alamat_wrap = "\n".join([alamat[i:i+50] for i in range(0, len(alamat), 50)])
    txt = f"NAMA: {nama}\nWAKTU: {w_skrg.strftime('%d/%m/%Y %H:%M:%S')}\nKOORDINAT: {lat}, {lon}\nALAMAT: {alamat_wrap}"
    
    f_size = int(img.width * 0.035)
    try:
        font = ImageFont.load_default(size=f_size)
    except:
        font = ImageFont.load_default()
    
    pos = (30, img.height - (img.height // 3))
    draw.multiline_text((pos[0]+2, pos[1]+2), txt, fill=(0, 0, 0), font=font, spacing=6)
    draw.multiline_text(pos, txt, fill=(255, 255, 255), font=font, spacing=6)
    
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

# --- SIDEBAR DENGAN JAM JALAN ---
with st.sidebar:
    st.header("🏢 MENU UTAMA")
    menu = st.selectbox("Pilih Layanan:", ["📍 Absensi", "📊 Rekap Absensi"])
    st.divider()
    
    # Placeholder untuk Jam Real-time
    jam_placeholder = st.empty()
    w_skrg = datetime.datetime.now() + datetime.timedelta(hours=7)
    jam_placeholder.markdown(f'''<div class="sidebar-box"><b>{w_skrg.strftime("%d %B %Y")}</b><br>
    <span style="font-size:20px; color:#3b82f6;">{w_skrg.strftime("%H:%M:%S")} WIB</span></div>''', unsafe_allow_html=True)

# --- HALAMAN ABSENSI ---
if menu == "📍 Absensi":
    st.markdown("<h2 style='text-align:center; color:white;'>Absensi Tim KI</h2>", unsafe_allow_html=True)
    
    loc_val = get_location_js()
    sesi = "MASUK" if 6 <= w_skrg.hour < 12 else "PULANG" if 12 <= w_skrg.hour < 23 else "TUTUP"
    
    if sesi == "TUTUP":
        st.error("🚫 Sesi Absensi sedang ditutup.")
    else:
        nama = st.selectbox("Pilih Nama:", ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"])
        foto = st.camera_input("Ambil Foto Wajah")
        
        # Validasi & Tombol Kirim
        if st.button("KIRIM ABSENSI SEKARANG", use_container_width=True, type="primary"):
            if not loc_val:
                st.warning("⚠️ LOKASI BELUM TERDETEKSI: Pastikan GPS HP aktif dan izinkan browser mengakses lokasi.")
            elif not foto:
                st.warning("⚠️ FOTO KOSONG: Silakan ambil foto terlebih dahulu melalui kamera di atas.")
            else:
                lat, lon = loc_val.get('lat'), loc_val.get('lon')
                with st.spinner("Mendeteksi Alamat Detail & Memproses Foto..."):
                    alamat_detail = get_address(lat, lon)
                    foto_final = process_watermark(foto, nama, lat, lon, alamat_detail, w_skrg)
                    
                    # Upload
                    try:
                        r_img = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": foto_final}).json()
                        link = r_img["data"]["url"]
                        payload = {"nama": nama, "tanggal": w_skrg.strftime("%Y-%m-%d"), "jam": w_skrg.strftime("%H:%M:%S"), "status": sesi, "foto_link": link, "lokasi": f"{lat}, {lon}\n{alamat_detail}"}
                        requests.post(WEBAPP_URL, json=payload, timeout=25)
                        st.success(f"✅ Berhasil! Selamat {sesi.lower()}, {nama}.")
                        time.sleep(2)
                        st.rerun()
                    except:
                        st.error("❌ Terjadi kesalahan pengiriman. Coba lagi.")

# --- HALAMAN REKAP ---
else:
    st.markdown("<h2 style='text-align:center; color:white;'>📊 Rekap Absensi Bulanan</h2>", unsafe_allow_html=True)
    list_bulan = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    col1, col2 = st.columns(2)
    with col1: b = st.selectbox("Pilih Bulan:", list_bulan, index=w_skrg.month - 1)
    with col2: y = st.selectbox("Pilih Tahun:", [2025, 2026, 2027], index=1)
        
    if st.button("🔍 Tampilkan Data Rekap", use_container_width=True):
        try:
            res = requests.get(f"{WEBAPP_URL}?bulan={b} {y}", timeout=25).json()
            if res:
                df = pd.DataFrame(res)
                df.insert(0, 'No', range(1, 1 + len(df)))
                st.dataframe(df, use_container_width=True, hide_index=True)
            else: st.info(f"Belum ada data untuk periode {b} {y}.")
        except: st.error("Gagal mengambil data dari Google Sheets.")

# Script untuk auto-refresh jam setiap 1 detik
components.html("""
    <script>
    window.parent.document.querySelector('section.main').scrollTo(0, 0);
    setTimeout(function(){ window.location.reload(); }, 60000); // Refresh tiap 1 menit untuk update jam
    </script>
""", height=0)
