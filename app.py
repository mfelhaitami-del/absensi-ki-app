import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image
import io
import numpy as np

# --- 1. KONFIGURASI ---
# Ganti dengan API Key ImgBB Anda jika perlu
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
# WAJIB: Ganti dengan URL Web App hasil Deployment "Anyone" terbaru
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwSBgnAIL--SekWYdcA8aoJXzdf3-_bX-dlI1KuLGkullXUWAAZwZ6w09In71hMkVWw/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# --- 2. CUSTOM CSS (Visual & Mirror Fix) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }

    /* Hanya membalik video live & preview foto di layar agar tidak mirror */
    [data-testid="stCameraInput"] video, 
    [data-testid="stCameraInput"] img {
        transform: scaleX(-1);
    }

    .stApp {
        background: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), 
                    url("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Logo_PU_%28RGB%29.jpg/960px-Logo_PU_%28RGB%29.jpg");
        background-size: cover; background-position: center; background-attachment: fixed;
    }
    
    [data-testid="stSidebar"] { background-color: rgba(15, 23, 42, 0.9) !important; backdrop-filter: blur(10px); }
    [data-testid="stSidebar"] * { color: white !important; }
    
    .sidebar-time-box { 
        background-color: rgba(255,255,255,0.1); padding: 15px; border-radius: 12px; 
        text-align: center; border: 1px solid #3b82f6; margin-bottom: 20px;
    }

    .hero-title { 
        font-size: 32px; font-weight: 800; text-align: center; 
        color: #ffffff; margin-bottom: 30px;
        text-shadow: 2px 4px 8px rgba(0,0,0,0.8);
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNGSI JAM WIB ---
@st.fragment(run_every="1s")
def jam_sidebar():
    # Menyesuaikan waktu ke WIB (UTC+7)
    waktu_skrg = datetime.datetime.now() + datetime.timedelta(hours=7)
    st.markdown(f"""
    <div class="sidebar-time-box">
        <span style="font-size: 14px;">{waktu_skrg.strftime('%d %B %Y')}</span><br>
        <span style="font-size: 26px; color: #3b82f6; font-weight: bold;">{waktu_skrg.strftime('%H:%M:%S')}</span><br>
        <b>WIB</b>
    </div>
    """, unsafe_allow_html=True)
    return waktu_skrg

# --- 4. NAVIGASI ---
with st.sidebar:
    st.markdown("### 🏢 MENU UTAMA")
    menu = st.selectbox("Pilih Layanan:", ["📍 Absensi", "📊 Rekap Absensi"])
    st.divider()
    w_aktif = jam_sidebar()

# --- 5. HALAMAN ABSENSI ---
if menu == "📍 Absensi":
    st.markdown('<p class="hero-title">Absensi Tim KI Satker PPS Banten</p>', unsafe_allow_html=True)
    
    # Logika Sesi Absen
    if 6 <= w_aktif.hour < 12: status_sesi = "MASUK"
    elif 12 <= w_aktif.hour < 23: status_sesi = "PULANG"
    else: status_sesi = "TUTUP"
    
    if status_sesi == "TUTUP":
        st.warning("⚠️ Sesi Absensi (06:00 - 23:00 WIB) sedang ditutup.")
    else:
        st.info(f"Sesi Aktif: **Absen {status_sesi}**")
        nama = st.selectbox("Pilih Nama:", [
            "Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", 
            "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", 
            "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"
        ])
        
        foto_raw = st.camera_input("Ambil Foto Wajah")
        
        if st.button("KIRIM DATA ABSENSI", use_container_width=True):
            if foto_raw:
                with st.spinner("Sedang mengirim data..."):
                    try:
                        # Pemrosesan Gambar: Flip secara fisik agar tidak mirror di database
                        img = Image.open(foto_raw).convert("RGB")
                        flipped_array = np.flip(np.array(img), axis=1)
                        img_final = Image.fromarray(flipped_array)
                        
                        buf = io.BytesIO()
                        img_final.save(buf, format="JPEG", quality=90)
                        
                        # 1. Upload ke ImgBB
                        res_img = requests.post(
                            f"https://api.imgbb.com/1/upload?key={API_IMGBB}", 
                            files={"image": buf.getvalue()}
                        ).json()
                        link_foto = res_img["data"]["url"]
                        
                        # 2. Kirim ke Google Sheets
                        payload = {
                            "nama": nama, 
                            "tanggal": w_aktif.strftime("%Y-%m-%d"), 
                            "jam": w_aktif.strftime("%H:%M:%S"), 
                            "status": status_sesi, 
                            "foto_link": link_foto
                        }
                        requests.post(WEBAPP_URL, json=payload, timeout=20)
                        
                        st.success(f"✅ Berhasil! Absen {status_sesi} telah tercatat.")
                        
                    except Exception as e:
                        st.error(f"❌ Terjadi kesalahan: {e}")
            else:
                st.warning("📸 Silakan ambil foto terlebih dahulu!")

# --- 6. HALAMAN REKAP ---
else:
    st.markdown('<p class="hero-title">📊 Rekap Absensi Bulanan</p>', unsafe_allow_html=True)
    
    list_bulan = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    c1, c2 = st.columns(2)
    with c1:
        p_bulan = st.selectbox("Pilih Bulan:", list_bulan, index=w_aktif.month - 1)
    with c2:
        p_tahun = st.selectbox("Pilih Tahun:", [2025, 2026, 2027], index=1)

    if st.button("🔍 Tampilkan Data Rekap", use_container_width=True):
        with st.spinner("Mengambil data..."):
            try:
                target_query = f"{p_bulan} {p_tahun}"
                # Request data dari Apps Script dengan parameter bulan
                response = requests.get(f"{WEBAPP_URL}?bulan={target_query}", timeout=25)
                data_json = response.json()
                
                if data_json and len(data_json) > 0:
                    df = pd.DataFrame(data_json)
                    # Menampilkan tabel data
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info(f"ℹ️ Tidak ada data absensi untuk periode {target_query}.")
            except Exception as e:
                st.error("❌ Gagal memuat data. Pastikan URL Deployment sudah benar dan diset ke 'Anyone'.")
