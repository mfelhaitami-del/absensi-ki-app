import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import numpy as np
import time
import streamlit.components.v1 as components

# --- CONFIG ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwsRsx5oIga72bOjgdg1UHU4u6Ds6-vPcbw7pHXCL7w37MBZ_ZpuNsEsVidvVmg0S2c/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# CSS: Tampilan Professional & Fix Mirror Kamera
st.markdown("""
    <style>
    [data-testid="stCameraInput"] video { transform: scaleX(-1); border-radius: 15px; border: 2px solid #3b82f6; }
    .stApp { background-color: #0e1117; }
    .sidebar-clock {
        background: rgba(255, 255, 255, 0.05);
        padding: 20px; border-radius: 15px; border: 1px solid #3b82f6; text-align: center;
    }
    .clock-time { font-size: 28px; font-weight: bold; color: #3b82f6; }
    </style>
""", unsafe_allow_html=True)

# --- JAVASCRIPT: GPS & JAM REALTIME ---
def inject_js_tools():
    return components.html("""
    <script>
    const send = (v) => window.parent.postMessage({type: 'streamlit:setComponentValue', value: v}, '*');
    
    // GPS Tracker
    function getGPS() {
        navigator.geolocation.getCurrentPosition(
            (p) => send({lat: p.coords.latitude, lon: p.coords.longitude, ok: true}),
            (e) => send({ok: false}),
            {enableHighAccuracy: true}
        );
    }
    getGPS();
    setInterval(getGPS, 10000); // Update tiap 10 detik

    // Jam Sidebar
    setInterval(() => {
        const now = new Date();
        const tStr = now.toLocaleTimeString('id-ID', {hour12: false}) + " WIB";
        const dStr = now.toLocaleDateString('id-ID', {weekday:'long', day:'numeric', month:'long', year:'numeric'});
        const elT = window.parent.document.getElementById('live-t');
        const elD = window.parent.document.getElementById('live-d');
        if(elT) elT.innerText = tStr;
        if(elD) elD.innerText = dStr;
    }, 1000);
    </script>
    """, height=0)

def fetch_address(lat, lon):
    try:
        r = requests.get(f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json", timeout=5).json()
        return r.get('display_name', 'Alamat tidak ditemukan')
    except: return "Lokasi Terdeteksi"

def draw_watermark(foto, nama, lat, lon, alamat, w_skrg):
    img = Image.open(foto).convert("RGB")
    img = ImageOps.mirror(img) # FIX MIRROR: Foto dibalik agar teks benar
    draw = ImageDraw.Draw(img)
    
    wrap_addr = "\n".join([alamat[i:i+50] for i in range(0, len(alamat), 50)])
    txt = f"PETUGAS: {nama}\nWAKTU: {w_skrg.strftime('%d/%m/%Y %H:%M:%S')}\nGPS: {lat}, {lon}\nALAMAT: {wrap_addr}"
    
    f_size = int(img.width * 0.035)
    try: font = ImageFont.load_default(size=f_size)
    except: font = ImageFont.load_default()
    
    pos = (20, img.height - (img.height // 3))
    draw.multiline_text((pos[0]+2, pos[1]+2), txt, fill=(0,0,0), font=font, spacing=5)
    draw.multiline_text(pos, txt, fill=(255,255,255), font=font, spacing=5)
    
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Logo_PU_%28RGB%29.jpg/200px-Logo_PU_%28RGB%29.jpg")
    st.markdown("""
        <div class="sidebar-clock">
            <div id="live-t" class="clock-time">00:00:00 WIB</div>
            <div id="live-d" style="color:white; font-size:14px;">Memuat...</div>
        </div>
    """, unsafe_allow_html=True)
    menu = st.selectbox("MENU UTAMA", ["📍 Absensi", "📊 Rekap Data"])
    w_skrg = datetime.datetime.now() + datetime.timedelta(hours=7)

js_data = inject_js_tools()

# --- HALAMAN ABSENSI ---
if menu == "📍 Absensi":
    st.markdown("<h2 style='text-align:center; color:white;'>Absensi Tim KI</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        nama = st.selectbox("Nama:", ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"])
        foto = st.camera_input("Ambil Foto Wajah")
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        gps_status = False
        if js_data and isinstance(js_data, dict) and js_data.get('ok'):
            st.success(f"✅ GPS Terkunci: {js_data['lat']}, {js_data['lon']}")
            gps_status = True
        else:
            st.warning("⚠️ Menunggu GPS... Pastikan izin lokasi AKTIF di browser.")

        if st.button("KIRIM ABSENSI", type="primary", use_container_width=True):
            if not gps_status:
                st.error("GPS belum terbaca!")
            elif not foto:
                st.error("Foto belum diambil!")
            else:
                with st.spinner("Memproses..."):
                    lat, lon = js_data['lat'], js_data['lon']
                    alamat = fetch_address(lat, lon)
                    foto_final = draw_watermark(foto, nama, lat, lon, alamat, w_skrg)
                    
                    try:
                        # Upload ImgBB
                        up = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": foto_final}).json()
                        link = up["data"]["url"]
                        
                        # Kirim GSheet
                        status = "MASUK" if w_skrg.hour < 12 else "PULANG"
                        payload = {"nama":nama, "tanggal":w_skrg.strftime("%Y-%m-%d"), "jam":w_skrg.strftime("%H:%M:%S"), "status":status, "foto_link":link, "lokasi":f"{lat},{lon} | {alamat}"}
                        requests.post(WEBAPP_URL, json=payload, timeout=15)
                        
                        st.balloons()
                        st.success("Absensi Berhasil Terkirim!")
                        time.sleep(2)
                        st.rerun()
                    except: st.error("Gagal mengirim data.")

# --- HALAMAN REKAP ---
else:
    st.markdown("<h2 style='text-align:center; color:white;'>📊 Rekap Absensi</h2>", unsafe_allow_html=True)
    list_b = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    c1, c2 = st.columns(2)
    with c1: bln = st.selectbox("Bulan", list_b, index=w_skrg.month - 1)
    with c2: thn = st.selectbox("Tahun", [2025, 2026], index=1)
    
    if st.button("Tampilkan Data", use_container_width=True):
        try:
            res = requests.get(f"{WEBAPP_URL}?bulan={bln} {thn}").json()
            if res: st.dataframe(pd.DataFrame(res), use_container_width=True, hide_index=True)
            else: st.warning("Data tidak ditemukan.")
        except: st.error("Gagal memuat data.")
