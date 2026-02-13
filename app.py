import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import numpy as np
import time

# --- KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxuH6AdWUeMkWagwsnYqhWO8_d_sgN0TO2TSBilPb7uiCFvx3MqoquFpx6TdAVmeLGV/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# --- CSS: BACKGROUND PU & KAMERA ---
st.markdown("""
    <style>
    /* Kamera tampilan layar (viewfinder) tidak mirror */
    [data-testid="stCameraInput"] video { transform: scaleX(-1); border-radius: 15px; border: 2px solid #3b82f6; }
    
    .stApp {
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
        url("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Logo_PU_%28RGB%29.jpg/960px-Logo_PU_%28RGB%29.jpg");
        background-size: cover; background-attachment: fixed;
    }
    .sidebar-box { 
        background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #3b82f6; 
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI WATERMARK & PROSES GAMBAR ---
def proses_gambar_absensi(foto, nama, w_skrg):
    try:
        # 1. Buka & Balik Gambar (Agar hasil akhir TIDAK mirror)
        img = Image.open(foto).convert("RGB")
        img = ImageOps.mirror(img)
        
        # 2. Siapkan Watermark
        draw = ImageDraw.Draw(img)
        hari_id = w_skrg.strftime("%A").replace("Monday","Senin").replace("Tuesday","Selasa").replace("Wednesday","Rabu").replace("Thursday","Kamis").replace("Friday","Jumat").replace("Saturday","Sabtu").replace("Sunday","Minggu")
        tgl_str = w_skrg.strftime(f"{hari_id}, %d %B %Y")
        jam_str = w_skrg.strftime("%H:%M:%S") + " WIB"
        
        watermark_text = f"{nama}\n{jam_str}\n{tgl_str}"
        
        # Ukuran font otomatis (3.5% dari lebar gambar)
        f_size = int(img.width * 0.035)
        try:
            font = ImageFont.load_default(size=f_size)
        except:
            font = ImageFont.load_default()

        # Posisi Kiri Bawah
        margin = 25
        # Gambar Bayangan Teks (Hitam)
        draw.multiline_text((margin+2, img.height - (f_size*4) + 2), watermark_text, fill=(0,0,0), font=font, spacing=5)
        # Gambar Teks Utama (Putih)
        draw.multiline_text((margin, img.height - (f_size*4)), watermark_text, fill=(255,255,255), font=font, spacing=5)
        
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        return buf.getvalue()
    except Exception as e:
        st.error(f"Gagal memproses gambar: {e}")
        return None

# --- FUNGSI KIRIM DATA ---
def kirim_data(nama, status, foto_bytes, w_skrg):
    try:
        # Upload ke ImgBB
        res_img = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": foto_bytes}).json()
        link_foto = res_img["data"]["url"]
        
        # Kirim ke Sheets
        payload = {
            "nama": nama, "tanggal": w_skrg.strftime("%Y-%m-%d"), 
            "jam": w_skrg.strftime("%H:%M:%S"), "status": status, "foto_link": link_foto
        }
        response = requests.post(WEBAPP_URL, json=payload, timeout=20)
        return response.status_code == 200
    except:
        return False

# --- DIALOG KONFIRMASI (WARNING) ---
@st.dialog("Konfirmasi Absensi")
def konfirmasi_dialog(nama, status, foto, w_skrg):
    st.warning("⚠️ Pastikan nama sudah benar sesuai identitas Anda!")
    st.write(f"Nama: **{nama}**")
    st.write(f"Sesi: **{status}**")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Ya, Kirim Sekarang", use_container_width=True, type="primary"):
            with st.status("Memproses watermark & mengirim...", expanded=False) as s:
                foto_final = proses_gambar_absensi(foto, nama, w_skrg)
                if foto_final and kirim_data(nama, status, foto_final, w_skrg):
                    s.update(label="✅ Berhasil Terkirim!", state="complete")
                    st.toast("Data absensi berhasil disimpan.", icon="✅")
                    time.sleep(2)
                    st.rerun()
                else:
                    s.update(label="❌ Gagal Mengirim!", state="error")
    with c2:
        if st.button("Batal", use_container_width=True):
            st.rerun()

# --- JAM SIDEBAR (FRAGMENT) ---
@st.fragment(run_every="1s")
def jam_sidebar():
    w = datetime.datetime.now() + datetime.timedelta(hours=7)
    st.markdown(f'''<div class="sidebar-box">
        <span style="color:white; font-size:14px;">{w.strftime("%d %B %Y")}</span><br>
        <span style="font-size:26px; color:#3b82f6; font-weight:bold;">{w.strftime("%H:%M:%S")}</span><br>
        <small style="color:white;">WIB</small>
    </div>''', unsafe_allow_html=True)
    return w

# --- UI SIDEBAR ---
with st.sidebar:
    st.header("🏢 MENU UTAMA")
    menu = st.selectbox("Layanan:", ["📍 Absensi", "📊 Rekap Absensi"])
    st.divider()
    w_skrg = jam_sidebar()

# --- HALAMAN ABSENSI ---
if menu == "📍 Absensi":
    st.markdown("<h2 style='text-align:center; color:white;'>Absensi Tim KI Satker PPS Banten</h2>", unsafe_allow_html=True)
    
    status_sesi = "MASUK" if 6 <= w_skrg.hour < 12 else "PULANG" if 12 <= w_skrg.hour < 23 else "TUTUP"
    
    if status_sesi == "TUTUP":
        st.error("🚫 Sesi Absensi ditutup (Aktif 06:00 - 23:00 WIB).")
    else:
        st.info(f"Sesi Aktif: **{status_sesi}**")
        nama = st.selectbox("Pilih Nama:", ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"])
        foto = st.camera_input("Ambil Foto Wajah")
        
        if st.button("KIRIM DATA ABSENSI", use_container_width=True, type="primary"):
            if foto:
                konfirmasi_dialog(nama, status_sesi, foto, w_skrg)
            else:
                st.warning("📸 Silakan ambil foto terlebih dahulu!")

# --- HALAMAN REKAP ---
else:
    st.markdown("<h2 style='text-align:center; color:white;'>📊 Rekap Absensi</h2>", unsafe_allow_html=True)
    list_b = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    c1, c2 = st.columns(2)
    b = c1.selectbox("Bulan:", list_b, index=w_skrg.month - 1)
    t = c2.selectbox("Tahun:", [2025, 2026], index=1)

    if st.button("🔍 Tampilkan Data", use_container_width=True):
        try:
            res = requests.get(f"{WEBAPP_URL}?bulan={b} {t}", timeout=25).json()
            if res:
                df = pd.DataFrame(res)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("Data belum tersedia.")
        except:
            st.error("Gagal mengambil data.")
