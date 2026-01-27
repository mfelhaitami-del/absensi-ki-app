import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image
from io import BytesIO

# --- 1. KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwKEM1F-kthxUFjIt_qc11U-98NEPLqD4g7nyl7TbHUA7H3QLSjchYC8U8bxSOxtuxM/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# --- 2. CUSTOM CSS (DENGAN BACKGROUND GAMBAR PILIHAN) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    
    /* Font Global */
    html, body, [class*="css"] {{ 
        font-family: 'Poppins', sans-serif; 
    }}

    /* SET BACKGROUND IMAGE */
    .stApp {{
        background: linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.5)), 
                    url("https://upload.wikimedia.org/wikipedia/commons/a/a7/Logo_PU_%28RGB%29.jpg");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    
    /* Sidebar Styling tetap gelap agar kontras */
    [data-testid="stSidebar"] {{ 
        background-color: rgba(15, 23, 42, 0.9) !important; 
        backdrop-filter: blur(10px);
    }}
    [data-testid="stSidebar"] * {{ color: white !important; }}
    
    /* Box Jam Sidebar */
    .sidebar-time-box {{ 
        background-color: rgba(255,255,255,0.1); 
        padding: 15px; border-radius: 12px; text-align: center; 
        border: 1px solid #3b82f6; margin-bottom: 20px;
    }}

    /* Judul Halaman */
    .hero-title {{ 
        font-size: 36px; font-weight: 800; text-align: center; 
        color: #ffffff; margin-top: -30px; margin-bottom: 30px;
        text-shadow: 2px 4px 8px rgba(0,0,0,0.8);
    }}

    /* Container Form & Tabel agar melayang (Glassmorphism) */
    [data-testid="stVerticalBlock"] > div {{
        background-color: rgba(0, 0, 0, 0.4);
        padding: 20px;
        border-radius: 15px;
        color: white;
    }}

    /* Menghilangkan bingkai putih pada tabel rekap */
    [data-testid="stDataFrame"] {{
        background-color: rgba(255, 255, 255, 0.1) !important;
        border: none !important;
    }}
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNGSI JAM REAL-TIME ---
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

# --- 4. NAVIGASI SIDEBAR (SISTEM DROPDOWN) ---
with st.sidebar:
    st.markdown("### 🏢 MENU UTAMA")
    
    menu = st.selectbox(
        "Pilih Layanan:", 
        ["📍 Absensi", "📊 Rekap Absensi"]
    )
    
    st.divider()
    waktu_aktif = jam_sidebar()

# --- 5. HALAMAN 1: PRESENSI ---
if menu == "📍 Absensi":
    st.markdown('<p class="hero-title">Absensi Tim KI Satker PPS Banten</p>', unsafe_allow_html=True)
    
    status_sesi = "TUTUP"
    if 6 <= waktu_aktif.hour < 12: status_sesi = "MASUK"
    elif 13 <= waktu_aktif.hour < 23: status_sesi = "PULANG"
    
    if status_sesi == "TUTUP":
        st.error(f"🚫 Sesi Absensi Tutup.")
    else:
        st.info(f"📍 Sesi: **Absen {status_sesi}**")
        nama = st.selectbox("Pilih Nama:", ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"])
        foto = st.camera_input("Ambil Foto Wajah")
        
        if st.button(f"KIRIM DATA ABSENSI", use_container_width=True):
            if foto:
                with st.spinner("Proses..."):
                    try:
                        res_img = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={{"image": foto.getvalue()}}).json()
                        link_foto = res_img["data"]["url"]
                        payload = {"nama": nama, "tanggal": waktu_aktif.strftime("%Y-%m-%d"), "jam": waktu_aktif.strftime("%H:%M:%S"), "status": status_sesi, "foto_link": link_foto}
                        requests.post(WEBAPP_URL, json=payload)
                        st.success("✅ Berhasil!")
                    except: 
                        st.error("Error mengirim data.")

# --- 6. HALAMAN 2: REKAP ABSENSI ---
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
            res = requests.get(f"{WEBAPP_URL}?bulan={{p_bulan}} {{p_tahun}}").json()
            if res:
                df = pd.DataFrame(res)
                df_tampil = df[["Nama", "Tanggal", "Jam Masuk", "Jam Pulang"]]
                df_tampil.index = range(1, len(df_tampil) + 1)
                
                st.write(f"### 📋 Laporan: {{p_bulan}} {{p_tahun}}")
                
                st.dataframe(
                    df_tampil, 
                    use_container_width=True, 
                    height=500
                )
            else:
                st.info("Data tidak ditemukan untuk periode ini.")
        except:
            st.error("Gagal mengambil data dari server.")
