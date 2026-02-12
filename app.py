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

# CSS: Glassmorphism & UI Premium
st.markdown("""
    <style>
    [data-testid="stCameraInput"] video { transform: scaleX(-1); border-radius: 20px; border: 4px solid #3b82f6; }
    .stApp {
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
        url("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Logo_PU_%28RGB%29.jpg/1200px-Logo_PU_%28RGB%29.jpg");
        background-size: cover; background-attachment: fixed;
    }
    .clock-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(15px);
        padding: 25px;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
    }
    .clock-time { font-size: 32px; font-weight: 800; color: #60a5fa; font-family: 'Segoe UI', sans-serif; }
    .clock-date { font-size: 15px; color: #e2e8f0; margin-top: 5px; font-weight: 500; }
    </style>
""", unsafe_allow_html=True)

# --- JALUR PINTAS GPS & JAM ---
def sync_browser_tools():
    # Menggunakan HTML/JS untuk GPS dan Jam Real-time
    return components.html("""
    <script>
    function sendToStreamlit(data) {
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: data
        }, '*');
    }

    // 1. Get Location
    navigator.geolocation.getCurrentPosition(
        (p) => sendToStreamlit({lat: p.coords.latitude, lon: p.coords.longitude, status: 'ok'}),
        (e) => sendToStreamlit({status: 'error', msg: e.message}),
        {enableHighAccuracy: true}
    );

    // 2. Real-time Clock Update
    setInterval(() => {
        const now = new Date();
        const timeStr = now.toLocaleTimeString('id-ID', {hour12: false}) + " WIB";
        const dateStr = now.toLocaleDateString('id-ID', {weekday:'long', day:'numeric', month:'long', year:'numeric'});
        
        const clockEl = window.parent.document.getElementById('live-clock');
        const dateEl = window.parent.document.getElementById('live-date');
        if(clockEl) clockEl.innerText = timeStr;
        if(dateEl) dateEl.innerText = dateStr;
    }, 1000);
    </script>
    """, height=0)

def fetch_address_text(lat, lon):
    try:
        r = requests.get(f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json", headers={'User-Agent':'AbsensiApp'}).json()
        return r.get('display_name', 'Lokasi Detail Tidak Terdeteksi')
    except: return "Koordinat Terdeteksi"

def draw_watermark(foto, nama, lat, lon, alamat, w_skrg):
    img = Image.open(foto).convert("RGB")
    img = Image.fromarray(np.flip(np.array(img), axis=1)) # Fix mirror
    draw = ImageDraw.Draw(img)
    
    # Text Setup
    addr_wrapped = "\n".join([alamat[i:i+45] for i in range(0, len(alamat), 45)])
    info = f"NAMA: {nama}\nWAKTU: {w_skrg.strftime('%d/%m/%Y %H:%M:%S')}\nGPS: {lat}, {lon}\nALAMAT: {addr_wrapped}"
    
    f_size = int(img.width * 0.038)
    try: font = ImageFont.load_default(size=f_size)
    except: font = ImageFont.load_default()
    
    pos = (35, img.height - (img.height // 3))
    # Draw Shadow
    draw.multiline_text((pos[0]+2, pos[1]+2), info, fill=(0,0,0), font=font, spacing=6)
    # Draw White Text
    draw.multiline_text(pos, info, fill=(255,255,255), font=font, spacing=6)
    
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

# --- UI SIDEBAR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Logo_PU_%28RGB%29.jpg/200px-Logo_PU_%28RGB%29.jpg")
    st.markdown("""
        <div class="clock-card">
            <div id="live-clock" class="clock-time">00:00:00 WIB</div>
            <div id="live-date" class="clock-date">Memuat Tanggal...</div>
        </div>
    """, unsafe_allow_html=True)
    menu = st.selectbox("LAYANAN", ["📍 Presensi Hadir", "📊 Rekap Data"])
    w_skrg = datetime.datetime.now() + datetime.timedelta(hours=7)

# Load Tools
browser_data = sync_browser_tools()

if menu == "📍 Presensi Hadir":
    st.markdown("<h2 style='text-align:center; color:white;'>Digital Attendance Tim KI</h2>", unsafe_allow_html=True)
    
    c1, c2 = st.columns([1, 1])
    with c1:
        nama = st.selectbox("Nama Personel:", ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"])
        foto = st.camera_input("Ambil Foto Presensi")
    
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        # Status GPS Safety Check
        if browser_data is None:
            st.info("⌛ Sedang menginisialisasi GPS... Mohon izinkan akses lokasi jika muncul notifikasi.")
            gps_ready = False
        elif browser_data.get('status') == 'ok':
            st.success(f"✅ GPS Terkunci: {browser_data['lat']:.4f}, {browser_data['lon']:.4f}")
            gps_ready = True
        else:
            st.error("❌ GPS Error: Mohon aktifkan GPS HP dan refresh halaman.")
            gps_ready = False

        if st.button("KIRIM DATA ABSEN", type="primary", use_container_width=True):
            if not gps_ready:
                st.warning("Mohon tunggu sampai GPS terkunci.")
            elif not foto:
                st.warning("Silakan ambil foto terlebih dahulu.")
            else:
                with st.spinner("Sedang memproses alamat dan mengirim data..."):
                    lat, lon = browser_data['lat'], browser_data['lon']
                    alamat = fetch_address_text(lat, lon)
                    foto_final = draw_watermark(foto, nama, lat, lon, alamat, w_skrg)
                    
                    try:
                        # Upload Image
                        up = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": foto_final}).json()
                        link = up["data"]["url"]
                        
                        # Save Data
                        sesi = "MASUK" if w_skrg.hour < 12 else "PULANG"
                        payload = {"nama":nama, "tanggal":w_skrg.strftime("%Y-%m-%d"), "jam":w_skrg.strftime("%H:%M:%S"), "status":sesi, "foto_link":link, "lokasi":f"{lat},{lon} | {alamat}"}
                        requests.post(WEBAPP_URL, json=payload, timeout=15)
                        
                        st.balloons()
                        st.success("Presensi Berhasil Dikirim!")
                        time.sleep(2)
                        st.rerun()
                    except: st.error("Koneksi gagal, silakan coba lagi.")

else:
    st.markdown("<h2 style='text-align:center; color:white;'>📊 Rekap Kehadiran</h2>", unsafe_allow_html=True)
    list_b = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    col_x, col_y = st.columns(2)
    with col_x: bln = st.selectbox("Bulan", list_b, index=w_skrg.month - 1)
    with col_y: thn = st.selectbox("Tahun", [2025, 2026, 2027], index=1)
    
    if st.button("Tampilkan Rekap", use_container_width=True):
        try:
            r = requests.get(f"{WEBAPP_URL}?bulan={bln} {thn}").json()
            if r: st.dataframe(pd.DataFrame(r), use_container_width=True, hide_index=True)
            else: st.warning("Data untuk bulan ini belum tersedia.")
        except: st.error("Gagal terhubung ke database.")
