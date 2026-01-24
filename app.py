import streamlit as st
import pandas as pd
import datetime
import requests
import time
from PIL import Image, ImageOps
from io import BytesIO

# --- KONFIGURASI ---
# Ganti dengan API Key ImgBB dan URL Web App Google Script Anda
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbyHMhEr0zy226CjIzHEGQJL0PUsMO3AI6EtZGUOTtDEX6DSqOKaRRrG1EE-eyVxXZES/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# --- CUSTOM CSS (FIX MIRROR & UI PREMIUM) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] { background-color: #1e293b !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    
    /* Judul Besar Putih */
    .hero-title { 
        font-size: 60px; 
        font-weight: 800; 
        color: #ffffff !important; 
        text-align: center; 
        text-shadow: 2px 2px 8px rgba(0,0,0,0.5); 
        margin-bottom: 0px; 
    }
    .hero-subtitle { font-size: 18px; color: #cbd5e1 !important; text-align: center; margin-bottom: 30px; }
    .welcome-text { font-size: 28px; font-weight: 600; color: #ffffff !important; margin-bottom: 10px; }
    
    /* FIX MIRROR KAMERA: Memaksa video tampil original (bukan mirror) */
    video { 
        transform: scaleX(1) !important; 
        -webkit-transform: scaleX(1) !important; 
        border-radius: 20px; 
        border: 3px solid #3b82f6; 
    }
    [data-testid="stCameraInput"] video {
        transform: scaleX(1) !important;
    }
    
    /* Button Styling */
    div.stButton > button { 
        width: 100%; 
        border-radius: 12px; 
        height: 3.5em; 
        background-color: #3b82f6; 
        color: white !important; 
        font-weight: 700; 
        font-size: 16px;
        border: none;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
    }
    
    /* Sidebar Time Box */
    .sidebar-time-box {
        background-color: rgba(255,255,255,0.1);
        padding: 12px;
        border-radius: 10px;
        margin-top: 10px;
        border: 1px solid rgba(255,255,255,0.2);
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI HALAMAN PRESENSI ---
def halaman_presensi(waktu_aktif, status_absen, tgl_skrg):
    st.markdown('<p class="hero-title">Absensi Tim KI</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">Sistem Pencatatan Kehadiran Digital Real-Time</p>', unsafe_allow_html=True)
    
    if status_absen == "TUTUP":
        st.error(f"🚫 Maaf, sesi absensi sedang ditutup. (Waktu sekarang: {waktu_aktif.strftime('%H:%M:%S')})")
    else:
        daftar_nama = [
            "Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", 
            "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", 
            "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda
