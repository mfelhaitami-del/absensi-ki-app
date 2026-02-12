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

# JUDUL TAB KEMBALI KE SEMULA
st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# CSS: Tampilan Elegan & Rapih
st.markdown("""
    <style>
    [data-testid="stCameraInput"] video { transform: scaleX(-1); border-radius: 15px; border: 3px solid #3b82f6; }
    .stApp {
        background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), 
        url("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Logo_PU_%28RGB%29.jpg/1200px-Logo_PU_%28RGB%29.jpg");
        background-size: cover; background-attachment: fixed;
    }
    /* Jam Digital Sidebar */
    .clock-box {
        background: rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #3b82f6;
        text-align: center;
        margin-bottom: 20px;
    }
    .t-main { font-size: 26px; font-weight: bold; color: #60a5fa; }
    .t-date { font-size: 14px; color: #ffffff; }
    </style>
""", unsafe_allow_html=True)

# --- JALUR PINTAS GPS & JAM (Perbaikan Error) ---
def sync_tools():
    return components.html("""
    <script>
    function send(data) {
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: data
        }, '*');
    }

    // Ambil GPS secara otomatis
    navigator.geolocation.getCurrentPosition(
        (p) => send({lat: p.coords.latitude, lon: p.coords.longitude, status: 'ok'}),
        (e) => send({status: 'error'}),
        {enableHighAccuracy: true}
    );

    // Update Jam Real-time
    setInterval(() => {
        const now = new Date();
        const tStr = now.toLocaleTimeString('id-ID', {hour12: false}) + " WIB";
        const dStr = now.toLocaleDateString('id-ID', {weekday:'long', day:'numeric', month:'long', year:'numeric'});
        
        const c = window.parent.document.getElementById('live-t');
        const d = window.parent.document.getElementById('live-d');
        if(c) c.innerText = tStr;
        if(d) d.innerText = dStr;
    }, 1000);
    </script>
    """, height=0)

def get_addr(lat, lon):
    try:
        r = requests.get(f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json", headers={'User-Agent':'AbsensiKI'}).json()
        return r.get('display_name', 'Alamat tidak ditemukan')
    except: return "Lokasi Terdeteksi"

def draw_info(foto, nama, lat, lon, alamat, w_skrg):
    img = Image.open(foto).convert("RGB")
    img = Image.fromarray(np.flip(np.array(img), axis=1)) # Fix Mirror
    draw = ImageDraw.Draw(img)
    
    # Wrap Alamat agar rapi
    wrap = "\n".join([alamat[i:i+45] for i in range(0, len(alamat), 45)])
    txt = f"NAMA: {nama}\nWAKTU: {w_skrg.strftime('%d/%m/%Y %H:%M:%S')}\nLOKASI: {lat}, {lon}\nALAMAT: {wrap}"
    
    f_size = int(img.width * 0.035)
    try: font = ImageFont.load_default(size=f_size)
    except: font = ImageFont.load_default()
    
    pos = (30, img.height - (img.height // 3))
    draw.multiline_text((pos[0]+2, pos[1]+2), txt, fill=(0,0,0), font=font, spacing=6)
    draw.multiline_text(pos, txt, fill=(255,255,255), font=font, spacing=6)
    
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Logo_PU_%28RGB%29.jpg/200px-Logo_PU_%28RGB%29.jpg")
    st.markdown("""
        <div class="clock-box">
            <div id="live-t" class="t-main">00:00:00 WIB</div>
            <div id="live-d" class="t-date">Memuat Hari...</div>
        </div>
    """, unsafe_allow_html=True)
    menu = st.selectbox("Layanan:", ["📍 Absensi", "📊 Rekap Absensi"])
    w_skrg = datetime.datetime.now() + datetime.timedelta(hours=7)

# Jalankan GPS & Jam
browser_data = sync_tools()

# --- HALAMAN ABSENSI ---
if menu == "📍 Absensi":
    st.markdown("<h2 style='text-align:center; color:white;'>Absensi Tim KI</h2>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        nama = st.selectbox("Pilih Nama:", ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"])
        foto = st.camera_input("Ambil Foto")
    
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        # PENGECEKAN GPS YANG AMAN (Mencegah StreamlitAPIException)
        gps_ok = False
        if browser_data is not None:
            if isinstance(browser_data, dict) and browser_data.get('status') == 'ok':
                st.success(f"✅ Lokasi Terdeteksi: {browser_data['lat']}, {browser_data['lon']}")
                gps_ok = True
            else:
                st.warning("📍 Sedang mendeteksi lokasi... Mohon izinkan GPS browser.")
        else:
            st.info("⌛ Menunggu sistem GPS...")

        if st.button("KIRIM DATA ABSENSI", type="primary", use_container_width=True):
            if not gps_ok:
                st.error("Gagal: Lokasi belum terdeteksi. Pastikan GPS aktif.")
            elif not foto:
                st.error("Gagal: Foto wajah belum diambil.")
            else:
                with st.spinner("Memproses alamat & foto..."):
                    lat, lon = browser_data['lat'], browser_data['lon']
                    alamat = get_addr(lat, lon)
                    foto_f = draw_info(foto, nama, lat, lon, alamat, w_skrg)
                    
                    try:
                        up = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": foto_f}).json()
                        link = up["data"]["url"]
                        
                        status = "MASUK" if w_skrg.hour < 12 else "PULANG"
                        payload = {"nama":nama, "tanggal":w_skrg.strftime("%Y-%m-%d"), "jam":w_skrg.strftime("%H:%M:%S"), "status":status, "foto_link":link, "lokasi":f"{lat},{lon} | {alamat}"}
                        requests.post(WEBAPP_URL, json=payload, timeout=15)
                        
                        st.balloons()
                        st.success(f"Absensi {status} Berhasil!")
                        time.sleep(2)
                        st.rerun()
                    except: st.error("Koneksi gagal. Coba beberapa saat lagi.")

# --- HALAMAN REKAP ---
else:
    st.markdown("<h2 style='text-align:center; color:white;'>📊 Rekap Absensi</h2>", unsafe_allow_html=True)
    list_b = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    col_x, col_y = st.columns(2)
    with col_x: bln = st.selectbox("Pilih Bulan:", list_b, index=w_skrg.month - 1)
    with col_y: thn = st.selectbox("Pilih Tahun:", [2025, 2026, 2027], index=1)
    
    if st.button("Tampilkan Rekap", use_container_width=True):
        try:
            r = requests.get(f"{WEBAPP_URL}?bulan={bln} {thn}").json()
            if r:
                df = pd.DataFrame(r)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else: st.warning("Data tidak ditemukan untuk periode ini.")
        except: st.error("Gagal mengambil data rekap.")
