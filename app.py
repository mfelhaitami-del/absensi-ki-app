import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image
import io
import numpy as np

# --- 1. KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbyxBvAFVWMYWCPTV-zi9ukIHyfnSbAVJvptDO7JP4WJdqNtQs8kLM7IhYXh9k-SSKCH/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# --- 2. CUSTOM CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }

    /* Fix Mirror Visual (Video & Snapshot) */
    [data-testid="stCameraInput"] video, 
    [data-testid="stCameraInput"] img {
        transform: scaleX(-1);
    }

    .stApp {
        background: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.6)), 
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
        color: #ffffff; margin-top: -30px; margin-bottom: 30px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNGSI JAM WIB ---
@st.fragment(run_every="1s")
def jam_sidebar():
    waktu_skrg = datetime.datetime.now() + datetime.timedelta(hours=7)
    st.markdown(f"""
    <div class="sidebar-time-box">
        <span style="font-size: 14px;">{waktu_skrg.strftime('%d %B %Y')}</span><br>
        <span style="font-size: 28px; color: #3b82f6; font-weight: bold;">{waktu_skrg.strftime('%H:%M:%S')}</span><br>
        <b>WIB</b>
    </div>
    """, unsafe_allow_html=True)
    return waktu_skrg

# --- 4. NAVIGASI ---
with st.sidebar:
    st.markdown("### 🏢 MENU UTAMA")
    menu = st.selectbox("Pilih Layanan:", ["📍 Absensi", "📊 Rekap Absensi"])
    st.divider()
    waktu_aktif = jam_sidebar()

# --- 5. HALAMAN ABSENSI ---
if menu == "📍 Absensi":
    st.markdown('<p class="hero-title">Absensi Tim KI Satker PPS Banten</p>', unsafe_allow_html=True)
    
    status_sesi = "TUTUP"
    if 6 <= waktu_aktif.hour < 12: status_sesi = "MASUK"
    elif 12 <= waktu_aktif.hour < 23: status_sesi = "PULANG"
    
    if status_sesi == "TUTUP":
        st.error(f"🚫 Sesi Absensi Tutup.")
    else:
        nama = st.selectbox("Pilih Nama:", ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"])
        foto_raw = st.camera_input("Ambil Foto Wajah")
        
        if st.button("KIRIM DATA ABSENSI", use_container_width=True):
            if foto_raw:
                with st.spinner("Memproses & Mengirim..."):
                    try:
                        img = Image.open(foto_raw).convert("RGB")
                        img_array = np.array(img)
                        flipped_array = np.flip(img_array, axis=1) 
                        img_final = Image.fromarray(flipped_array)
                        
                        buf = io.BytesIO()
                        img_final.save(buf, format="JPEG", quality=95)
                        byte_im = buf.getvalue()

                        res_img = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": ("absensi.jpg", byte_im, "image/jpeg")}).json()
                        link_foto = res_img["data"]["url"]
                        
                        payload = {
                            "nama": nama, "tanggal": waktu_aktif.strftime("%Y-%m-%d"), 
                            "jam": waktu_aktif.strftime("%H:%M:%S"), "status": status_sesi, "foto_link": link_foto
                        }
                        requests.post(WEBAPP_URL, json=payload, timeout=20)
                        st.success(f"✅ Berhasil! Absen {status_sesi} tercatat.")
                        
                    except Exception as e:
                        st.error(f"⚠️ Gagal mengirim: {e}")
            else:
                st.warning("📸 Ambil foto terlebih dahulu!")

# --- 6. HALAMAN REKAP ---
else:
    st.markdown('<p class="hero-title">📊 Rekap Absensi Bulanan</p>', unsafe_allow_html=True)
    
    # Pilihan Bulan dan Tahun untuk pencarian yang lebih akurat
    list_bulan = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    
    col1, col2 = st.columns(2)
    with col1:
        pilih_bulan = st.selectbox("Pilih Bulan:", list_bulan, index=waktu_aktif.month - 1)
    with col2:
        pilih_tahun = st.selectbox("Pilih Tahun:", [2025, 2026, 2027], index=1)

    if st.button("🔍 Tampilkan Data Rekap", use_container_width=True):
        with st.spinner("Mengambil data dari server..."):
            try:
                # Mengirim request dengan parameter bulan dan tahun
                # Contoh format yang dikirim: "February 2026"
                target_bulan = f"{pilih_bulan} {pilih_tahun}"
                res = requests.get(f"{WEBAPP_URL}?bulan={target_bulan}", timeout=25).json()
                
                if res and len(res) > 0:
                    df = pd.DataFrame(res)
                    # Pastikan nama kolom di Google Sheets sesuai (Case Sensitive)
                    # Contoh: Nama, Tanggal, Jam Masuk, Jam Pulang
                    st.dataframe(df, use_container_width=True)
                else:
                    st.warning(f"ℹ️ Tidak ada data untuk periode {target_bulan}.")
            except Exception as e:
                st.error(f"❌ Gagal memuat data. Pastikan URL Web App benar dan Apps Script sudah di-deploy ulang. (Error: {e})")
