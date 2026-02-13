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

# --- CSS: BACKGROUND & KAMERA FIX ---
st.markdown("""
    <style>
    /* Kamera di layar tetap mirror agar user nyaman (seperti cermin) */
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

# --- FUNGSI WATERMARK (DIBALIK AGAR TIDAK MIRROR) ---
def proses_gambar_final(foto, nama, status, w_skrg):
    try:
        # 1. Buka Gambar
        img = Image.open(foto).convert("RGB")
        
        # 2. BALIK GAMBAR (Anti-Mirror) agar hasil asli (bukan cermin)
        img = ImageOps.mirror(img)
        
        # 3. Buat Watermark
        draw = ImageDraw.Draw(img)
        hari_id = w_skrg.strftime("%A").replace("Monday","Senin").replace("Tuesday","Selasa").replace("Wednesday","Rabu").replace("Thursday","Kamis").replace("Friday","Jumat").replace("Saturday","Sabtu").replace("Sunday","Minggu")
        tgl_str = w_skrg.strftime(f"{hari_id}, %d %B %Y")
        jam_str = w_skrg.strftime("%H:%M:%S") + " WIB"
        
        # Teks Watermark (Ditambah STATUS)
        watermark_text = f"NAMA: {nama}\nSTATUS: {status}\nJAM: {jam_str}\nTANGGAL: {tgl_str}"
        
        # Ukuran font otomatis
        f_size = int(img.width * 0.035)
        try:
            font = ImageFont.load_default(size=f_size)
        except:
            font = ImageFont.load_default()

        # Posisi Kiri Bawah
        margin = 30
        y_pos = img.height - (f_size * 6) # Naikkan sedikit agar tidak mepet bawah
        
        # Shadow (Hitam)
        draw.multiline_text((margin+2, y_pos+2), watermark_text, fill=(0,0,0), font=font, spacing=5)
        # Teks Utama (Putih)
        draw.multiline_text((margin, y_pos), watermark_text, fill=(255,255,255), font=font, spacing=5)
        
        # Simpan ke buffer
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        return buf.getvalue()
    except Exception as e:
        st.error(f"Gagal memproses gambar: {e}")
        return None

# --- FUNGSI KIRIM DATA ---
def kirim_data(nama, status, foto_bytes, w_skrg):
    try:
        # Upload ImgBB
        res_img = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": foto_bytes}).json()
        link_foto = res_img["data"]["url"]
        
        # Kirim Sheets
        payload = {
            "nama": nama, "tanggal": w_skrg.strftime("%Y-%m-%d"), 
            "jam": w_skrg.strftime("%H:%M:%S"), "status": status, "foto_link": link_foto
        }
        response = requests.post(WEBAPP_URL, json=payload, timeout=20)
        return response.status_code == 200
    except:
        return False

# --- DIALOG KONFIRMASI ---
@st.dialog("Konfirmasi Absensi")
def konfirmasi_dialog(nama, status, foto, w_skrg):
    st.warning("⚠️ Pastikan nama sudah benar!")
    st.write(f"Nama: **{nama}**")
    st.write(f"Sesi: **{status}**")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Ya, Sudah Benar", use_container_width=True, type="primary"):
            with st.status("Sedang memproses foto & mengirim...", expanded=False) as s:
                # Proses gambar dibalik + watermark status
                foto_final = proses_gambar_final(foto, nama, status, w_skrg)
                if foto_final and kirim_data(nama, status, foto_final, w_skrg):
                    s.update(label="✅ Berhasil!", state="complete")
                    st.toast(f"Terima kasih {nama}, absen {status} berhasil!", icon="✅")
                    time.sleep(3)
                    st.rerun()
                else:
                    s.update(label="❌ Gagal kirim!", state="error")
    with col2:
        if st.button("Tidak, Ganti", use_container_width=True):
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

# --- UI UTAMA ---
with st.sidebar:
    st.header("🏢 MENU")
    menu = st.selectbox("Layanan:", ["📍 Absensi", "📊 Rekap"])
    st.divider()
    w_skrg = jam_sidebar()

if menu == "📍 Absensi":
    st.markdown("<h2 style='text-align:center; color:white;'>Absensi Tim KI Satker PPS Banten</h2>", unsafe_allow_html=True)
    
    # Sesi Otomatis
    status_sesi = "MASUK" if 6 <= w_skrg.hour < 12 else "PULANG" if 12 <= w_skrg.hour < 23 else "TUTUP"
    
    if status_sesi == "TUTUP":
        st.error("🚫 Absensi Tutup (Buka 06:00 - 23:00 WIB)")
    else:
        st.info(f"Sesi Aktif: **{status_sesi}**")
        nama_user = st.selectbox("Pilih Nama:", ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"])
        
        foto_input = st.camera_input("Ambil Foto")
        
        if st.button("KIRIM DATA ABSENSI", use_container_width=True, type="primary"):
            if foto_input:
                konfirmasi_dialog(nama_user, status_sesi, foto_input, w_skrg)
            else:
                st.warning("📸 Silakan ambil foto dulu!")

else:
    st.markdown("<h2 style='text-align:center; color:white;'>📊 Rekap Bulanan</h2>", unsafe_allow_html=True)
    # Fitur rekap Anda tetap di sini...
    st.info("Gunakan tombol tampilkan data rekap untuk melihat histori.")
