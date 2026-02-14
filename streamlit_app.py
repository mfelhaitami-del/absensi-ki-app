import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import numpy as np
import time

# --- KONFIGURASI ---
# Ganti dengan API Key ImgBB Anda
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
# Pastikan URL ini adalah URL /exec dari Deployment Apps Script TERBARU Anda
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwsiCIyYlxm_e2xqI8prV-qFZ6-y4UFwJeoWH1B8sGqADxb8Nrm1CMIwLXZh9BUm7hp/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# --- CSS: BACKGROUND & KAMERA ANTI-MIRROR ---
st.markdown("""
    <style>
    /* Viewfinder kamera tetap mirror agar user nyaman */
    [data-testid="stCameraInput"] video, [data-testid="stCameraInput"] img { transform: scaleX(-1); }
    .stApp {
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
        url("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Logo_PU_%28RGB%29.jpg/960px-Logo_PU_%28RGB%29.jpg");
        background-size: cover; background-attachment: fixed;
    }
    .sidebar-box { background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #3b82f6; }
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI WATERMARK & PROSES GAMBAR (POJOK KIRI BAWAH) ---
def proses_gambar_watermark(foto, nama, status, w_skrg):
    try:
        # 1. Buka Gambar & Balik Horizontal (Anti-Mirror agar hasil foto normal & tulisan terbaca)
        img = Image.open(foto).convert("RGB")
        img = ImageOps.mirror(img)
        
        # 2. Siapkan Objek Draw
        draw = ImageDraw.Draw(img)
        
        # 3. Format Teks Watermark
        hari_id = w_skrg.strftime("%A").replace("Monday","Senin").replace("Tuesday","Selasa").replace("Wednesday","Rabu").replace("Thursday","Kamis").replace("Friday","Jumat").replace("Saturday","Sabtu").replace("Sunday","Minggu")
        tgl_str = w_skrg.strftime(f"{hari_id}, %d %B %Y")
        jam_str = w_skrg.strftime("%H:%M:%S") + " WIB"
        
        watermark_text = f"NAMA: {nama}\nSTATUS: {status}\nJAM: {jam_str}\nTANGGAL: {tgl_str}"
        
        # 4. Pengaturan Font
        font_size = int(img.width * 0.035)
        try:
            # Menggunakan font default sistem
            font = ImageFont.load_default() 
        except:
            font = ImageFont.load_default()

        # 5. Tentukan Posisi (Pojok Kiri Bawah)
        margin = 25
        # Hitung tinggi blok teks (estimasi 4 baris)
        text_height_total = font_size * 5 
        y_position = img.height - text_height_total - margin
        
        # 6. Gambar Teks (Bayangan hitam dulu agar teks putih kontras)
        draw.multiline_text((margin + 2, y_position + 2), watermark_text, fill=(0, 0, 0), font=font, spacing=5)
        draw.multiline_text((margin, y_position), watermark_text, fill=(255, 255, 255), font=font, spacing=5)
        
        # 7. Simpan ke Buffer
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        return buf.getvalue()
    except Exception as e:
        st.error(f"Gagal memproses watermark: {e}")
        return None

# --- FUNGSI KIRIM DATA ---
def kirim_ke_sheets(nama, status, foto_bytes, w_skrg):
    try:
        # 1. Upload ke ImgBB
        r_img = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": foto_bytes}).json()
        link = r_img["data"]["url"]
        
        # 2. Payload untuk Apps Script (Sesuai format spreadsheet baru)
        payload = {
            "nama": nama, 
            "tanggal": w_skrg.strftime("%Y-%m-%d"), 
            "jam": w_skrg.strftime("%H:%M:%S"), 
            "status": status, 
            "foto_link": link
        }
        response = requests.post(WEBAPP_URL, json=payload, timeout=20)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error Pengiriman: {e}")
        return False

# --- POP-UP DIALOG KONFIRMASI ---
@st.dialog("Konfirmasi Absensi")
def konfirmasi_dialog(nama, status_sesi, foto, w_skrg):
    st.warning("⚠️ Pastikan nama sudah benar sesuai nama anda!")
    st.write(f"Nama Terpilih: **{nama}**")
    st.write(f"Sesi: **{status_sesi}**")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Ya, Sudah Benar", use_container_width=True, type="primary"):
            with st.status("Sedang memproses & mengirim data...", expanded=False) as s:
                # Proses Watermark (Anti-Mirror + Teks Kiri Bawah)
                foto_final = proses_gambar_watermark(foto, nama, status_sesi, w_skrg)
                
                if foto_final:
                    sukses = kirim_ke_sheets(nama, status_sesi, foto_final, w_skrg)
                    if sukses:
                        s.update(label="✅ Absen Berhasil Terkirim!", state="complete", expanded=False)
                        st.toast(f"Berhasil! Foto telah di-watermark & dikirim.", icon='✅')
                        time.sleep(3)
                        st.rerun()
                    else:
                        s.update(label="❌ Gagal mengirim data!", state="error")
                else:
                    s.update(label="❌ Gagal mengolah foto!", state="error")

    with col2:
        if st.button("Tidak, Batal", use_container_width=True):
            st.rerun()

# --- JAM REAL-TIME DI SIDEBAR ---
@st.fragment(run_every="1s")
def jam_sidebar():
    # Menyesuaikan waktu ke WIB (UTC+7)
    w = datetime.datetime.now() + datetime.timedelta(hours=7)
    st.markdown(f'''<div class="sidebar-box"><span style="color:white">{w.strftime("%d %B %Y")}</span><br>
    <span style="font-size:24px; color:#3b82f6; font-weight:bold;">{w.strftime("%H:%M:%S")}</span><br>
    <small style="color:white">WIB</small></div>''', unsafe_allow_html=True)
    return w

# --- STRUKTUR SIDEBAR ---
with st.sidebar:
    st.header("🏢 MENU UTAMA")
    menu = st.selectbox("Layanan:", ["📍 Absensi", "📊 Rekap Absensi"])
    st.divider()
    w_skrg = jam_sidebar()

# --- HALAMAN 📍 ABSENSI ---
if menu == "📍 Absensi":
    st.markdown("<h2 style='text-align:center; color:white;'>Absensi Tim KI Satker PPS Banten</h2>", unsafe_allow_html=True)
    
    # Penentuan Sesi secara otomatis
    status_sesi = "MASUK" if 6 <= w_skrg.hour < 12 else "PULANG" if 12 <= w_skrg.hour < 23 else "TUTUP"
    
    if status_sesi == "TUTUP":
        st.error("🚫 Sesi Absensi sedang ditutup (Aktif 06:00 - 23:00 WIB).")
    else:
        st.info(f"Sesi Aktif saat ini: **{status_sesi}**")
        nama = st.selectbox("Pilih Nama Anda:", [
            "Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", 
            "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", 
            "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"
        ])
        
        foto = st.camera_input("Ambil Foto Wajah")
        
        if st.button("KIRIM DATA ABSENSI", use_container_width=True, type="primary"):
            if foto:
                konfirmasi_dialog(nama, status_sesi, foto, w_skrg)
            else:
                st.warning("📸 Silakan ambil foto terlebih dahulu!")

# --- HALAMAN 📊 REKAP ABSENSI ---
else:
    st.markdown("<h2 style='text-align:center;'>📊 Rekap Absensi Bulanan</h2>", unsafe_allow_html=True)
    
    # ... (bagian pilih bulan dan tahun) ...

    if st.button("🔍 Tampilkan Data Rekap", use_container_width=True):
        try:
            res = requests.get(f"{WEBAPP_URL}?bulan={b} {t}", timeout=25).json()
            if res:
                df = pd.DataFrame(res)
                # Tambahkan nomor urut agar lebih rapi
                df.insert(0, 'No', range(1, 1 + len(df)))
                
                st.table(df) # Menggunakan st.table agar statis dan rapi
            else:
                st.info(f"Data periode {b} {t} belum tersedia.")
        except:
            st.error("Gagal mengambil data. Pastikan URL Apps Script sudah benar.")
