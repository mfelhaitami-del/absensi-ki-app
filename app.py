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

# CSS: Desain Elegan & Jam Modern
st.markdown("""
    <style>
    [data-testid="stCameraInput"] video { transform: scaleX(-1); border-radius: 15px; border: 3px solid #3b82f6; }
    [data-testid="stCameraInput"] img { transform: scaleX(-1); border-radius: 15px; }
    
    .stApp {
        background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), 
        url("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Logo_PU_%28RGB%29.jpg/960px-Logo_PU_%28RGB%29.jpg");
        background-size: cover; background-attachment: fixed;
    }
    
    /* Sidebar Clock Styling */
    .clock-container {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .clock-time { font-size: 28px; font-weight: bold; color: #3b82f6; font-family: 'Courier New', monospace; }
    .clock-date { font-size: 14px; color: #aaa; text-transform: uppercase; letter-spacing: 1px; }
    </style>
""", unsafe_allow_html=True)

# --- JALUR PINTAS GPS & JAM (Auto-Prompt) ---
def sync_tools():
    # Komponen ini akan memaksa browser meminta lokasi begitu di-render
    return components.html("""
    <div id="root"></div>
    <script>
    // 1. Force Geolocation Prompt
    function askLocation() {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                window.parent.postMessage({
                    type: 'streamlit:setComponentValue',
                    value: {lat: pos.coords.latitude, lon: pos.coords.longitude, ok: true}
                }, '*');
            },
            (err) => {
                window.parent.postMessage({
                    type: 'streamlit:setComponentValue',
                    value: {ok: false, msg: err.message}
                }, '*');
            },
            { enableHighAccuracy: true, timeout: 5000 }
        );
    }
    askLocation();

    // 2. Real-time Clock for Sidebar
    setInterval(() => {
        const now = new Date();
        const tStr = now.toLocaleTimeString('id-ID', {hour12: false});
        const dStr = now.toLocaleDateString('id-ID', {weekday:'long', day:'numeric', month:'long', year:'numeric'});
        
        const sideClock = window.parent.document.getElementById('js-clock');
        const sideDate = window.parent.document.getElementById('js-date');
        if(sideClock) sideClock.innerText = tStr + " WIB";
        if(sideDate) sideDate.innerText = dStr;
    }, 1000);
    </script>
    """, height=0)

# --- ALAMAT API ---
def fetch_address(lat, lon):
    try:
        res = requests.get(f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json", headers={'User-Agent':'PPS-Banten-App'}).json()
        return res.get('display_name', 'Alamat Detail Tidak Tersedia')
    except: return "Koordinat Terdeteksi (Gagal memuat teks alamat)"

# --- WATERMARK ---
def make_watermark(foto, nama, lat, lon, alamat, w_skrg):
    img = Image.open(foto).convert("RGB")
    img = Image.fromarray(np.flip(np.array(img), axis=1)) # Fix Mirror
    draw = ImageDraw.Draw(img)
    
    # Wrap Alamat
    wrap_addr = "\n".join([alamat[i:i+50] for i in range(0, len(alamat), 50)])
    txt = f"PETUGAS: {nama}\nWAKTU: {w_skrg.strftime('%d/%m/%Y %H:%M:%S')}\nPOSISI: {lat}, {lon}\nALAMAT: {wrap_addr}"
    
    f_size = int(img.width * 0.035)
    try: font = ImageFont.load_default(size=f_size)
    except: font = ImageFont.load_default()
    
    pos = (30, img.height - (img.height // 3))
    draw.multiline_text((pos[0]+2, pos[1]+2), txt, fill=(0,0,0), font=font, spacing=5)
    draw.multiline_text(pos, txt, fill=(255,255,255), font=font, spacing=5)
    
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

# --- APP LAYOUT ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Logo_PU_%28RGB%29.jpg/200px-Logo_PU_%28RGB%29.jpg")
    st.markdown("""
        <div class="clock-container">
            <div id="js-date" class="clock-date">Memuat Tanggal...</div>
            <div id="js-clock" class="clock-time">00:00:00 WIB</div>
        </div>
    """, unsafe_allow_html=True)
    menu = st.selectbox("Menu Layanan", ["📍 Presensi Kehadiran", "📊 Laporan Bulanan"])
    w_skrg = datetime.datetime.now() + datetime.timedelta(hours=7)

# Load JS Tools
data_gps = sync_tools()

if menu == "📍 Presensi Kehadiran":
    st.markdown("<h2 style='text-align:center; color:white;'>Presensi Digital Tim KI</h2>", unsafe_allow_html=True)
    
    col_a, col_b = st.columns([1, 1])
    with col_a:
        nama = st.selectbox("Pilih Personel:", ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"])
        foto = st.camera_input("Silakan Foto Wajah")
    
    with col_b:
        st.info("💡 **Petunjuk:** Pastikan wajah terlihat jelas. Sistem akan otomatis menyertakan lokasi detail dan koordinat GPS pada foto Anda.")
        if not data_gps:
            st.warning("📍 **Menunggu GPS...** Jika tidak muncul permintaan lokasi, pastikan fitur Lokasi/GPS di HP Anda sudah aktif dan refresh halaman.")
        else:
            st.success("📍 **GPS Terkunci:** Lokasi Anda sudah terdeteksi.")
        
        if st.button("KIRIM PRESENSI", type="primary", use_container_width=True):
            if not data_gps or not data_gps.get('ok'):
                st.error("Gagal mengirim: Lokasi tidak ditemukan. Izinkan akses GPS browser.")
            elif not foto:
                st.error("Gagal mengirim: Ambil foto terlebih dahulu.")
            else:
                with st.spinner("Mengirim data ke pusat..."):
                    lat, lon = data_gps['lat'], data_gps['lon']
                    alamat = fetch_address(lat, lon)
                    foto_f = make_watermark(foto, nama, lat, lon, alamat, w_skrg)
                    
                    try:
                        # Upload Foto
                        up = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": foto_f}).json()
                        link = up["data"]["url"]
                        
                        # Simpan Data
                        status = "MASUK" if w_skrg.hour < 12 else "PULANG"
                        payload = {"nama":nama, "tanggal":w_skrg.strftime("%Y-%m-%d"), "jam":w_skrg.strftime("%H:%M:%S"), "status":status, "foto_link":link, "lokasi":f"{lat},{lon} | {alamat}"}
                        requests.post(WEBAPP_URL, json=payload, timeout=15)
                        
                        st.balloons()
                        st.success(f"Presensi {status} Berhasil Dikirim!")
                        time.sleep(2)
                        st.rerun()
                    except: st.error("Koneksi bermasalah, silakan coba lagi.")

else:
    st.markdown("<h2 style='text-align:center; color:white;'>📊 Laporan Absensi</h2>", unsafe_allow_html=True)
    list_b = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    c1, c2 = st.columns(2)
    with c1: bln = st.selectbox("Bulan", list_b, index=w_skrg.month - 1)
    with c2: thn = st.selectbox("Tahun", [2025, 2026, 2027], index=1)
    
    if st.button("Tampilkan Rekap", use_container_width=True):
        try:
            r = requests.get(f"{WEBAPP_URL}?bulan={bln} {thn}").json()
            if r: st.table(pd.DataFrame(r))
            else: st.warning("Data belum tersedia untuk periode ini.")
        except: st.error("Gagal memuat database.")
