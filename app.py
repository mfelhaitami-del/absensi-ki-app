import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image, ImageDraw, ImageFont # Import ImageFont
import io
import numpy as np
import time

# --- KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
# GANTI URL DI BAWAH INI DENGAN URL WEB APP ANDA SENDIRI
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzkEK1hwvMukLWk0oP8dTerPl1XFYpVO7LnTyJvxC61liDUQ_47zlvgwnVbs4Hw6gEb/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# CSS: Styling & Background
st.markdown("""
    <style>
    /* Mengatasi kamera mirror */
    [data-testid="stCameraInput"] video { transform: scaleX(-1); }
    [data-testid="stCameraInput"] img { transform: scaleX(-1); }
    
    .stApp {
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
        url("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Logo_PU_%28RGB%29.jpg/960px-Logo_PU_%28RGB%29.jpg");
        background-size: cover; background-attachment: fixed;
    }
    .sidebar-box { 
        background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; 
        text-align: center; border: 1px solid #3b82f6; color: white; 
    }
    </style>
""", unsafe_allow_html=True)

# Fungsi Watermark
def process_watermark(foto, nama, w_skrg):
    img = Image.open(foto).convert("RGB")
    # Balik gambar secara horizontal agar tidak mirror
    img = Image.fromarray(np.flip(np.array(img), axis=1))
    draw = ImageDraw.Draw(img)
    
    # Coba memuat font default, jika gagal pakai default Pillow
    try:
        font_path = "arial.ttf" # Coba font umum di sistem Linux
        font = ImageFont.truetype(font_path, 28)
    except IOError:
        font = ImageFont.load_default()
    
    # Text info
    txt = f"NAMA: {nama}\nWAKTU: {w_skrg.strftime('%d/%m/%Y %H:%M:%S')}\nSTATUS: TERVERIFIKASI"
    
    # Posisi teks di pojok kiri bawah
    pos = (20, img.height - 100)
    
    # Tambah bayangan teks hitam
    draw.multiline_text((pos[0]+2, pos[1]+2), txt, fill=(0, 0, 0), font=font)
    # Teks utama putih
    draw.multiline_text(pos, txt, fill=(255, 255, 255), font=font)
    
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

# Fungsi Kirim Data
def kirim_data(nama, status, foto_bytes, w_skrg):
    try:
        # Upload ke ImgBB
        r_img = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": foto_bytes}).json()
        link = r_img["data"]["url"]
        
        # Kirim ke Sheets
        payload = {
            "nama": nama, "tanggal": w_skrg.strftime("%Y-%m-%d"), 
            "jam": w_skrg.strftime("%H:%M:%S"), "status": status, 
            "foto_link": link
        }
        requests.post(WEBAPP_URL, json=payload, timeout=20)
        return True
    except requests.exceptions.Timeout:
        st.error("Waktu koneksi habis. Coba lagi.")
        return False
    except requests.exceptions.RequestException as e:
        st.error(f"Gagal koneksi: {e}. Coba lagi.")
        return False
    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
        return False

# Sidebar
with st.sidebar:
    st.header("🏢 MENU")
    menu = st.selectbox("Pilih Layanan:", ["📍 Absensi", "📊 Rekap"])
    st.divider()
    w_skrg = datetime.datetime.now() + datetime.timedelta(hours=7)
    st.markdown(f'''<div class="sidebar-box"><b>{w_skrg.strftime("%d %B %Y")}</b><br>
    <span style="font-size:22px; color:#3b82f6;">{w_skrg.strftime("%H:%M:%S")} WIB</span></div>''', unsafe_allow_html=True)

# Halaman Absensi
if menu == "📍 Absensi":
    st.markdown("<h2 style='text-align:center; color:white;'>Absensi Tim KI Satker PPS Banten</h2>", unsafe_allow_html=True)
    
    sesi = "MASUK" if 6 <= w_skrg.hour < 12 else "PULANG" if 12 <= w_skrg.hour < 23 else "TUTUP"
    
    if sesi == "TUTUP":
        st.error("🚫 Absensi sudah ditutup hari ini.")
    else:
        nama = st.selectbox("Nama Karyawan:", ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"])
        foto = st.camera_input("Ambil Foto Presensi")
        
        if st.button("KIRIM ABSENSI SEKARANG", use_container_width=True):
            if foto:
                with st.spinner("Sedang memproses dan mengunggah data..."):
                    foto_final = process_watermark(foto, nama, w_skrg)
                    if kirim_data(nama, sesi, foto_final, w_skrg):
                        st.success(f"✅ Berhasil! Selamat {sesi.lower()}, {nama}.")
                        time.sleep(2)
                        st.rerun()
                    # Error message sudah ditangani di fungsi kirim_data
            else:
                st.warning("📸 Foto harus diambil terlebih dahulu!")

# Halaman Rekap
else:
    st.markdown("<h2 style='text-align:center; color:white;'>📊 Rekap Absensi</h2>", unsafe_allow_html=True)
    
    list_bulan = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    current_year = w_skrg.year
    # Buat list tahun dari 2023 sampai tahun sekarang + 1
    list_tahun = list(range(2023, current_year + 2)) 
    
    # Pilihan Bulan dan Tahun
    col_bulan, col_tahun = st.columns(2)
    with col_bulan:
        b = st.selectbox("Bulan:", list_bulan, index=w_skrg.month - 1)
    with col_tahun:
        y = st.selectbox("Tahun:", list_tahun, index=list_tahun.index(current_year))
    
    if st.button("🔍 Tampilkan Data Rekap", use_container_width=True):
        bulan_tahun_query = f"{b} {y}"
        try:
            with st.spinner(f"Mengambil data rekap bulan {bulan_tahun_query}..."):
                res = requests.get(f"{WEBAPP_URL}?bulan={bulan_tahun_query}", timeout=25).json()
            
            if res:
                df = pd.DataFrame(res)
                df.insert(0, 'No', range(1, 1 + len(df)))
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info(f"Data absensi untuk {bulan_tahun_query} tidak ditemukan.")
        except requests.exceptions.Timeout:
            st.error("Waktu koneksi habis. Coba lagi.")
        except requests.exceptions.RequestException as e:
            st.error(f"Gagal koneksi ke server: {e}. Coba lagi.")
        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")
