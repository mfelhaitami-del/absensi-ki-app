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

# CSS: Tampilan & Mirror Kamera
st.markdown("""
    <style>
    [data-testid="stCameraInput"] video { transform: scaleX(-1); }
    [data-testid="stCameraInput"] img { transform: scaleX(-1); }
    .stApp {
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
        url("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Logo_PU_%28RGB%29.jpg/960px-Logo_PU_%28RGB%29.jpg");
        background-size: cover; background-attachment: fixed;
    }
    .sidebar-box { background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #3b82f6; color: white; margin-bottom: 20px;}
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI ALAMAT (Tanpa Geopy) ---
def get_detail_alamat(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        response = requests.get(url, headers={'User-Agent': 'AbsensiApp/1.0'}).json()
        return response.get('display_name', 'Alamat tidak ditemukan')
    except:
        return "Gagal mengambil alamat detail"

# --- JS: GPS & JAM REALTIME ---
def inject_tools():
    components.html("""
    <script>
    // 1. Ambil GPS
    navigator.geolocation.getCurrentPosition((pos) => {
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: {lat: pos.coords.latitude, lon: pos.coords.longitude}
        }, '*');
    });

    // 2. Jam Berdetik di Sidebar
    setInterval(() => {
        const now = new Date();
        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' };
        const str = now.toLocaleDateString('id-ID', options) + ' WIB';
        const el = window.parent.document.querySelector('.sidebar-box');
        if (el) el.innerHTML = `<b>JAM DIGITAL</b><br><span style="font-size:20px; color:#3b82f6;">${str}</span>`;
    }, 1000);
    </script>
    """, height=0)

# --- FUNGSI WATERMARK ---
def apply_watermark(foto, nama, lat, lon, alamat, w_skrg):
    img = Image.open(foto).convert("RGB")
    img = Image.fromarray(np.flip(np.array(img), axis=1)) # Fix mirror
    draw = ImageDraw.Draw(img)
    
    # Bungkus teks alamat
    limit = 45
    alamat_wrap = "\n".join([alamat[i:i+limit] for i in range(0, len(alamat), limit)])
    txt = f"NAMA: {nama}\nWAKTU: {w_skrg.strftime('%d/%m/%Y %H:%M:%S')}\nKOORDINAT: {lat}, {lon}\nALAMAT: {alamat_wrap}"
    
    f_size = int(img.width * 0.038)
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
    st.header("🏢 MENU")
    menu = st.selectbox("Layanan:", ["📍 Absensi", "📊 Rekap Data"])
    st.divider()
    # Box Jam (akan diupdate oleh JS)
    st.markdown('<div class="sidebar-box">Memuat Jam...</div>', unsafe_allow_html=True)
    w_skrg = datetime.datetime.now() + datetime.timedelta(hours=7)

# --- HALAMAN UTAMA ---
loc_val = inject_tools()

if menu == "📍 Absensi":
    st.markdown("<h2 style='text-align:center; color:white;'>Presensi Tim KI</h2>", unsafe_allow_html=True)
    
    nama = st.selectbox("Pilih Nama:", ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"])
    foto = st.camera_input("Ambil Foto")
    
    if st.button("KIRIM ABSENSI", type="primary", use_container_width=True):
        if not loc_val:
            st.warning("⚠️ LOKASI BELUM TERDETEKSI: Mohon izinkan akses GPS browser dan tunggu sejenak.")
        elif not foto:
            st.warning("⚠️ FOTO KOSONG: Ambil foto wajah Anda terlebih dahulu.")
        else:
            with st.spinner("Sedang memproses lokasi & alamat..."):
                lat, lon = loc_val['lat'], loc_val['lon']
                alamat = get_detail_alamat(lat, lon)
                foto_final = apply_watermark(foto, nama, lat, lon, alamat, w_skrg)
                
                # Upload
                try:
                    r_img = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": foto_final}).json()
                    link = r_img["data"]["url"]
                    
                    status_absen = "MASUK" if 6 <= w_skrg.hour < 12 else "PULANG"
                    payload = {"nama": nama, "tanggal": w_skrg.strftime("%Y-%m-%d"), "jam": w_skrg.strftime("%H:%M:%S"), "status": status_absen, "foto_link": link, "lokasi": f"{lat}, {lon} | {alamat}"}
                    requests.post(WEBAPP_URL, json=payload, timeout=20)
                    
                    st.success(f"✅ Berhasil Absen {status_absen}!")
                    time.sleep(2)
                    st.rerun()
                except:
                    st.error("Gagal mengirim data. Cek koneksi.")

else:
    st.markdown("<h2 style='text-align:center; color:white;'>📊 Rekap Absensi</h2>", unsafe_allow_html=True)
    list_b = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    c1, c2 = st.columns(2)
    with c1: bln = st.selectbox("Bulan:", list_b, index=w_skrg.month - 1)
    with c2: thn = st.selectbox("Tahun:", [2025, 2026, 2027], index=1)
    
    if st.button("Tampilkan Data", use_container_width=True):
        try:
            res = requests.get(f"{WEBAPP_URL}?bulan={bln} {thn}", timeout=20).json()
            if res:
                df = pd.DataFrame(res)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else: st.info("Data tidak ditemukan.")
        except: st.error("Gagal memuat data dari Spreadsheet.")
