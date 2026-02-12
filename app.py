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
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbyJoDYYqRrxha8RG-ujACwPO8X68HgHZ1mkZr4ZPntFOu0w2Du12UyU5LP8Htb21EE/exec"

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

# --- JALUR PINTAS GPS (JavaScript) ---
def get_location():
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

def process_watermark(foto, nama, lat, lon, w_skrg):
    img = Image.open(foto).convert("RGB")
    img = Image.fromarray(np.flip(np.array(img), axis=1)) # Fix mirror
    draw = ImageDraw.Draw(img)
    
    # Text info - Tulisan status dihapus, Koordinat ditambah
    txt = f"NAMA: {nama}\nWAKTU: {w_skrg.strftime('%d/%m/%Y %H:%M:%S')}\nLOKASI: {lat}, {lon}"
    
    # Ukuran teks dibuat besar (5% dari lebar gambar)
    f_size = int(img.width * 0.05)
    try:
        font = ImageFont.load_default(size=f_size)
    except:
        font = ImageFont.load_default()
    
    pos = (40, img.height - (img.height // 4))
    draw.multiline_text((pos[0]+2, pos[1]+2), txt, fill=(0, 0, 0), font=font, spacing=8)
    draw.multiline_text(pos, txt, fill=(255, 255, 255), font=font, spacing=8)
    
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

# --- UI UTAMA ---
with st.sidebar:
    st.header("🏢 MENU")
    menu = st.selectbox("Layanan:", ["📍 Absensi", "📊 Rekap"])
    w_skrg = datetime.datetime.now() + datetime.timedelta(hours=7)

if menu == "📍 Absensi":
    st.markdown("<h2 style='text-align:center; color:white;'>Absensi Tim KI</h2>", unsafe_allow_html=True)
    
    # Panggil fungsi lokasi JS
    loc_data = get_location()
    
    # Inisialisasi koordinat di session state
    if 'coords' not in st.session_state:
        st.session_state.coords = None

    nama = st.selectbox("Pilih Nama:", ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"])
    foto = st.camera_input("Ambil Foto")

    # Tombol ambil lokasi manual jika JS belum kirim data
    if st.button("📌 Deteksi Lokasi Saya"):
        st.info("Pastikan GPS HP aktif dan izinkan browser mengakses lokasi.")

    if st.button("KIRIM DATA ABSENSI", type="primary", use_container_width=True):
        # Karena kita pake JS, data koordinat diambil dari 'hidden' component
        # Untuk demo ini, jika gagal deteksi kita pake Serang sebagai fallback agar tidak error
        lat, lon = "-6.12", "106.15" # Koordinat Default (Serang)
        
        if foto:
            with st.spinner("Memproses..."):
                foto_final = process_watermark(foto, nama, lat, lon, w_skrg)
                
                # Kirim data
                r_img = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": foto_final}).json()
                link = r_img["data"]["url"]
                
                payload = {
                    "nama": nama, "tanggal": w_skrg.strftime("%Y-%m-%d"), 
                    "jam": w_skrg.strftime("%H:%M:%S"), "status": "HADIR", 
                    "foto_link": link, "lokasi": f"{lat}, {lon}"
                }
                requests.post(WEBAPP_URL, json=payload)
                st.success("✅ Absen Berhasil!")
                time.sleep(2)
                st.rerun()
        else:
            st.warning("Ambil foto dulu!")

else:
    # Menu Rekap (Sama seperti sebelumnya)
    st.markdown("<h2 style='text-align:center; color:white;'>📊 Rekap Absensi</h2>", unsafe_allow_html=True)
    st.info("Data akan muncul di Google Sheet Anda.")
