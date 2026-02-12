import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image, ImageOps
import io

# --- 1. KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbw3AtbN2Znxq1XJDEYHkgQqC-G8SU_7RcwptjmzzS9dXNyd5iK8d-Kk3cKaODfl_FrC/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# --- 2. CUSTOM CSS (PREVIEW MIRROR & UI) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }

    /* CSS agar tampilan kamera di layar HP/Laptop seperti cermin */
    [data-testid="stCameraInput"] video {
        transform: scaleX(-1);
    }

    .stApp {
        background: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.6)), 
                    url("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Logo_PU_%28RGB%29.jpg/960px-Logo_PU_%28RGB%29.jpg");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    
    [data-testid="stSidebar"] { 
        background-color: rgba(15, 23, 42, 0.9) !important; 
        backdrop-filter: blur(10px);
    }
    [data-testid="stSidebar"] * { color: white !important; }
    
    .sidebar-time-box { 
        background-color: rgba(255,255,255,0.1); 
        padding: 15px; border-radius: 12px; text-align: center; 
        border: 1px solid #3b82f6; margin-bottom: 20px;
    }

    .hero-title { 
        font-size: 32px; font-weight: 800; text-align: center; 
        color: #ffffff; margin-top: -30px; margin-bottom: 30px;
        text-shadow: 2px 4px 8px rgba(0,0,0,0.8);
    }

    [data-testid="stDataFrame"] {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNGSI JAM WIB ---
@st.fragment(run_every="1s")
def jam_sidebar():
    # Menambah 7 jam untuk konversi ke WIB jika server menggunakan UTC
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
        st.error(f"🚫 Sesi Absensi Tutup (06:00 - 23:00 WIB).")
    else:
        st.info(f"📍 Sesi Sekarang: **Absen {status_sesi}**")
        nama = st.selectbox("Pilih Nama Anda:", [
            "Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", 
            "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", 
            "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"
        ])
        
        foto = st.camera_input("Ambil Foto Wajah")
        
        if st.button("KIRIM DATA ABSENSI", use_container_width=True):
            if foto:
                with st.spinner("🔄 Sedang memproses gambar (Flip Horizontal)..."):
                    try:
                        # --- PROSES FLIP GAMBAR AGAR HASIL TIDAK TERBALIK ---
                        # Membuka gambar asli
                        img_raw = Image.open(foto)
                        
                        # Menggunakan transpose FLIP_LEFT_RIGHT untuk membalikkan posisi
                        # Ini akan memastikan tulisan/background tidak mirror di hasil akhir
                        img_corrected = img_raw.transpose(Image.FLIP_LEFT_RIGHT)
                        
                        # Simpan ke byte stream
                        img_buffer = io.BytesIO()
                        img_corrected.save(img_buffer, format="JPEG", quality=90)
                        final_bytes = img_buffer.getvalue()

                        # 1. Upload ke ImgBB
                        payload_img = {"image": ("absensi.jpg", final_bytes, "image/jpeg")}
                        res_img = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files=payload_img).json()
                        link_foto = res_img["data"]["url"]
                        
                        # 2. Payload ke Google Sheets
                        payload_data = {
                            "nama": nama, 
                            "tanggal": waktu_aktif.strftime("%Y-%m-%d"), 
                            "jam": waktu_aktif.strftime("%H:%M:%S"), 
                            "status": status_sesi, 
                            "foto_link": link_foto
                        }
                        
                        response = requests.post(WEBAPP_URL, json=payload_data, timeout=20)
                        
                        if response.status_code == 200:
                            st.success(f"✅ Berhasil! Foto sudah normal (tidak mirror) dan data terkirim.")
                        else:
                            st.error("Gagal terhubung ke Database Google Sheets.")
                            
                    except Exception as e:
                        st.error(f"⚠️ Kesalahan Sistem: {e}")
            else:
                st.warning("📸 Silakan ambil foto terlebih dahulu!")

# --- 6. HALAMAN REKAP ---
else:
    st.markdown('<p class="hero-title">📊 Rekap Kehadiran Bulanan</p>', unsafe_allow_html=True)
    bulan_indo = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    
    c1, c2 = st.columns(2)
    with c1:
        p_bulan = st.selectbox("Pilih Bulan", bulan_indo, index=waktu_aktif.month - 1)
    with c2:
        p_tahun = st.selectbox("Pilih Tahun", [2025, 2026], index=1)
    
    if st.button("🔍 Tampilkan Rekap Data", use_container_width=True):
        try:
            fetch_url = f"{WEBAPP_URL}?bulan={p_bulan} {p_tahun}"
            res = requests.get(fetch_url, timeout=20).json()
            
            if res:
                df = pd.DataFrame(res)
                df_tampil = df[["Nama", "Tanggal", "Jam Masuk", "Jam Pulang"]]
                df_tampil.index = range(1, len(df_tampil) + 1)
                st.dataframe(df_tampil, use_container_width=True, height=500)
            else:
                st.info(f"Data rekap untuk {p_bulan} {p_tahun} belum tersedia.")
        except:
            st.error("Gagal mengambil data dari Google Sheets.")
