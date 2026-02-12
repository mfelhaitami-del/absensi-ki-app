import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import numpy as np
import time
import streamlit.components.v1 as components

# --- KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbyJoDYYqRrxha8RG-ujACwPO8X68HgHZ1mkZr4ZPntFOu0w2Du12UyU5LP8Htb21EE/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# CSS: Perbaikan Tampilan & Fix Mirror Viewport
st.markdown("""
    <style>
    /* Membuat tampilan kamera di layar tidak mirror agar nyaman saat berpose */
    [data-testid="stCameraInput"] video { transform: scaleX(-1); border-radius: 10px; border: 2px solid #3b82f6; }
    .stApp {
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
        url("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Logo_PU_%28RGB%29.jpg/1200px-Logo_PU_%28RGB%29.jpg");
        background-size: cover; background-attachment: fixed;
    }
    .jam-box {
        background: rgba(255, 255, 255, 0.1);
        padding: 15px; border-radius: 12px; border: 1px solid #3b82f6; text-align: center; color: white;
    }
    </style>
""", unsafe_allow_html=True)

# --- JALUR PINTAS GPS & JAM (Murni JavaScript) ---
def tools_javascript():
    return components.html("""
    <script>
    const send = (v) => window.parent.postMessage({type: 'streamlit:setComponentValue', value: v}, '*');
    
    // Auto-update Jam Sidebar
    setInterval(() => {
        const n = new Date();
        const tStr = n.toLocaleTimeString('id-ID') + " WIB";
        const dStr = n.toLocaleDateString('id-ID', {weekday:'long', day:'numeric', month:'long', year:'numeric'});
        const elT = window.parent.document.getElementById('j-clock');
        const elD = window.parent.document.getElementById('j-date');
        if(elT) elT.innerText = tStr;
        if(elD) elD.innerText = dStr;
    }, 1000);

    // Memaksa permintaan GPS ke Browser
    navigator.geolocation.getCurrentPosition(
        (p) => send({lat: p.coords.latitude, lon: p.coords.longitude, ok: true}),
        (e) => send({ok: false}),
        {enableHighAccuracy: true, timeout: 5000}
    );
    </script>
    """, height=0)

def get_alamat_lengkap(lat, lon):
    try:
        r = requests.get(f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json", headers={'User-Agent':'AbsensiKI'}).json()
        return r.get('display_name', 'Alamat tidak ditemukan')
    except: return "Lokasi Terdeteksi"

def proses_foto(foto, nama, lat, lon, alamat, w_skrg):
    img = Image.open(foto).convert("RGB")
    # FIX MIRROR: Membalikkan gambar agar posisi teks di belakang tidak terbalik
    img = ImageOps.mirror(img)
    draw = ImageDraw.Draw(img)
    
    wrap_alamat = "\n".join([alamat[i:i+45] for i in range(0, len(alamat), 45)])
    txt = f"NAMA: {nama}\nWAKTU: {w_skrg.strftime('%d/%m/%Y %H:%M:%S')}\nGPS: {lat}, {lon}\nALAMAT: {wrap_alamat}"
    
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
        <div class="jam-box">
            <div id="j-clock" style="font-size:24px; font-weight:bold; color:#60a5fa;">00:00:00 WIB</div>
            <div id="j-date" style="font-size:13px;">Memuat...</div>
        </div>
    """, unsafe_allow_html=True)
    menu = st.selectbox("Layanan:", ["📍 Absensi", "📊 Rekap Absensi"])
    w_skrg = datetime.datetime.now() + datetime.timedelta(hours=7)

js_data = tools_javascript()

# --- HALAMAN ABSENSI ---
if menu == "📍 Absensi":
    st.markdown("<h2 style='text-align:center; color:white;'>Absensi Tim KI</h2>", unsafe_allow_html=True)
    
    nama = st.selectbox("Pilih Nama:", ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"])
    foto = st.camera_input("Ambil Foto Wajah")
    
    # STATUS GPS SAFETY CHECK
    gps_siap = False
    if js_data and isinstance(js_data, dict) and js_data.get('ok'):
        st.success(f"📍 GPS Aktif: {js_data['lat']}, {js_data['lon']}")
        gps_siap = True
    else:
        st.warning("⚠️ LOKASI BELUM TERDETEKSI: Klik 'Izinkan' pada notifikasi browser di atas.")

    if st.button("KIRIM DATA ABSENSI", type="primary", use_container_width=True):
        if not gps_siap:
            st.error("Gagal: Lokasi belum terkunci. Mohon izinkan GPS browser.")
        elif not foto:
            st.error("Gagal: Foto wajah belum diambil.")
        else:
            with st.spinner("Memproses data..."):
                lat, lon = js_data['lat'], js_data['lon']
                alamat = get_alamat_lengkap(lat, lon)
                foto_final = proses_foto(foto, nama, lat, lon, alamat, w_skrg)
                
                try:
                    up = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": foto_final}).json()
                    link = up["data"]["url"]
                    
                    status = "MASUK" if w_skrg.hour < 12 else "PULANG"
                    payload = {"nama":nama, "tanggal":w_skrg.strftime("%Y-%m-%d"), "jam":w_skrg.strftime("%H:%M:%S"), "status":status, "foto_link":link, "lokasi":f"{lat},{lon} | {alamat}"}
                    requests.post(WEBAPP_URL, json=payload, timeout=15)
                    
                    st.success(f"Berhasil! Selamat {status.lower()}, {nama}.")
                    time.sleep(2)
                    st.rerun()
                except: st.error("Gagal mengirim ke database. Cek koneksi.")

# --- HALAMAN REKAP ---
else:
    st.markdown("<h2 style='text-align:center; color:white;'>📊 Rekap Absensi</h2>", unsafe_allow_html=True)
    list_b = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    c1, c2 = st.columns(2)
    with c1: bln = st.selectbox("Bulan:", list_b, index=w_skrg.month - 1)
    with c2: thn = st.selectbox("Tahun:", [2025, 2026], index=1)
    
    if st.button("Tampilkan Rekap", use_container_width=True):
        try:
            r = requests.get(f"{WEBAPP_URL}?bulan={bln} {thn}").json()
            if r: st.dataframe(pd.DataFrame(r), use_container_width=True, hide_index=True)
            else: st.info("Data belum tersedia.")
        except: st.error("Gagal mengambil data.")
