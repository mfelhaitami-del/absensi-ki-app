import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image, ImageDraw
import io
import numpy as np
import time
from streamlit_js_eval import get_geolocation

# --- KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
# PASTI KAN URL INI ADALAH URL DEPLOYMENT TERBARU DARI APPS SCRIPT
WEBAPP_URL = "https://script.google.com/macros/s/AKfycby5qnV3tyb7Zp7PB54kXI46vHTopAK8VRY03_XWjiuVpTHyK8lc7H5oYX0U4VVmEDV8/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# CSS: Background & Kamera Anti-Mirror
st.markdown("""
    <style>
    [data-testid="stCameraInput"] video, [data-testid="stCameraInput"] img { transform: scaleX(-1); }
    .stApp {
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
        url("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Logo_PU_%28RGB%29.jpg/960px-Logo_PU_%28RGB%29.jpg");
        background-size: cover; background-attachment: fixed;
    }
    .sidebar-box { background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #3b82f6; }
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI WATERMARK ---
def process_watermark(foto, nama, lat, lon, w_skrg):
    img = Image.open(foto).convert("RGB")
    # Balik horizontal karena kamera streamlit mirror
    img = Image.fromarray(np.flip(np.array(img), axis=1))
    
    draw = ImageDraw.Draw(img)
    txt = f"Nama: {nama}\nWaktu: {w_skrg.strftime('%d/%m/%Y %H:%M:%S')}\nLokasi: {lat}, {lon}"
    
    # Posisi teks (pojok kiri bawah)
    pos = (15, img.height - 85)
    # Gambar bayangan hitam agar teks putih terbaca di background terang
    draw.multiline_text((pos[0]+1, pos[1]+1), txt, fill=(0, 0, 0))
    draw.multiline_text(pos, txt, fill=(255, 255, 255))
    
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

# --- FUNGSI KIRIM DATA ---
def kirim_data(nama, status, foto_bytes, lokasi_str, w_skrg):
    try:
        r_img = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": foto_bytes}).json()
        link = r_img["data"]["url"]
        
        payload = {
            "nama": nama, "tanggal": w_skrg.strftime("%Y-%m-%d"), 
            "jam": w_skrg.strftime("%H:%M:%S"), "status": status, 
            "foto_link": link, "lokasi": lokasi_str
        }
        requests.post(WEBAPP_URL, json=payload, timeout=20)
        return True
    except:
        return False

# --- DIALOG KONFIRMASI ---
@st.dialog("Konfirmasi Absensi")
def konfirmasi_dialog(nama, status, foto, lokasi_str, w_skrg):
    st.warning("⚠️ Pastikan nama sudah benar sesuai nama anda!")
    st.write(f"Nama: **{nama}**")
    st.write(f"Sesi: **{status}**")
    st.write(f"Koordinat: `{lokasi_str}`")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Ya, Sudah Benar", use_container_width=True, type="primary"):
            with st.status("Memproses data & lokasi...", expanded=False) as s:
                lat, lon = lokasi_str.split(", ")
                foto_final = process_watermark(foto, nama, lat, lon, w_skrg)
                
                if kirim_data(nama, status, foto_final, lokasi_str, w_skrg):
                    s.update(label="✅ Absen Berhasil Terkirim!", state="complete")
                    st.toast(f"Terima kasih {nama}!", icon='✅')
                    time.sleep(3)
                    st.rerun()
                else:
                    s.update(label="❌ Gagal Terkirim!", state="error")
    with col2:
        if st.button("Tidak, Ganti Nama", use_container_width=True):
            st.rerun()

# --- SIDEBAR ---
@st.fragment(run_every="1s")
def jam_sidebar():
    w = datetime.datetime.now() + datetime.timedelta(hours=7)
    st.markdown(f'''<div class="sidebar-box"><span style="color:white">{w.strftime("%d %B %Y")}</span><br>
    <span style="font-size:24px; color:#3b82f6; font-weight:bold;">{w.strftime("%H:%M:%S")}</span><br>
    <small style="color:white">WIB</small></div>''', unsafe_allow_html=True)
    return w

with st.sidebar:
    st.header("🏢 MENU UTAMA")
    menu = st.selectbox("Layanan:", ["📍 Absensi", "📊 Rekap Absensi"])
    st.divider()
    w_skrg = jam_sidebar()

# --- HALAMAN ABSENSI ---
if menu == "📍 Absensi":
    # Minta izin lokasi dari browser
    loc = get_geolocation()
    
    st.markdown("<h2 style='text-align:center; color:white;'>Absensi Tim KI Satker PPS Banten</h2>", unsafe_allow_html=True)
    status_sesi = "MASUK" if 6 <= w_skrg.hour < 12 else "PULANG" if 12 <= w_skrg.hour < 23 else "TUTUP"
    
    if status_sesi == "TUTUP":
        st.error("🚫 Sesi Absensi sedang ditutup.")
    else:
        nama = st.selectbox("Pilih Nama:", ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"])
        foto = st.camera_input("Ambil Foto Wajah")
        
        if st.button("KIRIM DATA ABSENSI", use_container_width=True):
            if not loc:
                st.error("📍 Akses Lokasi diperlukan! Mohon izinkan lokasi di browser Anda lalu refresh.")
            elif foto:
                lat = loc['coords']['latitude']
                lon = loc['coords']['longitude']
                lokasi_str = f"{lat}, {lon}"
                konfirmasi_dialog(nama, status_sesi, foto, lokasi_str, w_skrg)
            else:
                st.warning("📸 Silakan ambil foto terlebih dahulu!")

# --- HALAMAN REKAP ---
else:
    st.markdown("<h2 style='text-align:center; color:white;'>📊 Rekap Absensi Bulanan</h2>", unsafe_allow_html=True)
    list_b = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    b = st.selectbox("Pilih Bulan:", list_b, index=w_skrg.month - 1)
    
    if st.button("🔍 Tampilkan Data Rekap", use_container_width=True):
        try:
            res = requests.get(f"{WEBAPP_URL}?bulan={b} 2026", timeout=25).json()
            if res:
                df = pd.DataFrame(res)
                df.insert(0, 'No', range(1, 1 + len(df)))
                st.dataframe(df[['No', 'Nama', 'Tanggal', 'Jam Masuk', 'Jam Pulang']], hide_index=True, use_container_width=True, 
                             column_config={"No": st.column_config.Column(width=40), "Nama": st.column_config.Column(width="large")})
            else:
                st.info("Belum ada data untuk bulan ini.")
        except:
            st.error("Gagal terhubung ke database.")
