import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image
from io import BytesIO

# --- KONFIGURASI (GANTI DENGAN MILIK ANDA) ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwKEM1F-kthxUFjIt_qc11U-98NEPLqD4g7nyl7TbHUA7H3QLSjchYC8U8bxSOxtuxM/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# --- CUSTOM CSS (FIX WARNA PUTIH) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
    
    [data-testid="stSidebar"] { background-color: #0f172a !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    
    .sidebar-time-box { 
        background-color: rgba(255,255,255,0.1); 
        padding: 15px; border-radius: 12px; text-align: center; 
        border: 1px solid #3b82f6; margin-bottom: 20px;
    }

    .hero-title { 
        font-size: 30px; font-weight: 800; text-align: center; 
        color: #ffffff; margin-top: -50px; margin-bottom: 20px;
    }

    /* Tabel Rekap: Paksa Teks Hitam agar terlihat di latar Putih */
    .stTable {
        background-color: white !important;
        color: #1e293b !important;
        border-radius: 10px;
    }
    .stTable td, .stTable th {
        color: #1e293b !important;
        border-bottom: 1px solid #e2e8f0 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI JAM OTOMATIS ---
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

# --- NAVIGASI ---
with st.sidebar:
    st.header("🏢 Dashboard KI")
    menu = st.radio("Navigasi", ["📍 Presensi Wajah", "📊 Rekap Absensi"])
    st.divider()
    waktu_aktif = jam_sidebar()

# --- HALAMAN 1: PRESENSI ---
if menu == "📍 Presensi Wajah":
    st.markdown('<p class="hero-title">Absensi Tim KI Satker PPS Banten</p>', unsafe_allow_html=True)
    
    # Penentuan Sesi
    status_sesi = "TUTUP"
    if 6 <= waktu_aktif.hour < 12: status_sesi = "MASUK"
    elif 13 <= waktu_aktif.hour < 23: status_sesi = "PULANG"
    
    if status_sesi == "TUTUP":
        st.error(f"🚫 Sesi Tutup. (Sekarang: {waktu_aktif.strftime('%H:%M:%S')} WIB)")
    else:
        st.info(f"📍 Sesi: **Absen {status_sesi}**")
        nama = st.selectbox("Pilih Nama:", ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"])
        foto = st.camera_input("Ambil Foto Wajah")
        
        if st.button(f"🚀 Kirim Absen {status_sesi}", use_container_width=True):
            if foto:
                with st.spinner("Proses Kirim Data..."):
                    try:
                        # Upload ImgBB
                        res_img = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": foto.getvalue()}).json()
                        link_foto = res_img["data"]["url"]
                        
                        # Kirim Sheets
                        payload = {
                            "nama": nama, "tanggal": waktu_aktif.strftime("%Y-%m-%d"),
                            "jam": waktu_aktif.strftime("%H:%M:%S"), "status": status_sesi, "foto_link": link_foto
                        }
                        requests.post(WEBAPP_URL, json=payload)
                        st.success("✅ Berhasil Absen!")
                        st.balloons()
                    except: st.error("Gagal mengirim data.")
            else: st.warning("⚠️ Ambil foto dulu!")

# --- HALAMAN 2: REKAP ---
else:
    st.markdown('<p class="hero-title">Rekap Absensi</p>', unsafe_allow_html=True)
    bulan_indo = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    c1, c2 = st.columns(2)
    with c1: b = st.selectbox("Bulan", bulan_indo, index=waktu_aktif.month - 1)
    with c2: t = st.selectbox("Tahun", [2025, 2026], index=1)
    
    if st.button("🔍 Tampilkan Rekap", use_container_width=True):
        try:
            res = requests.get(f"{WEBAPP_URL}?bulan={b} {t}").json()
            if res:
                df = pd.DataFrame(res)
                # Tampilkan kolom utama saja
                df_final = df[["Nama", "Tanggal", "Jam Masuk", "Jam Pulang"]]
                df_final.index = range(1, len(df_final) + 1)
                st.table(df_final)
            else: st.info("Tidak ada data.")
        except: st.error("Gagal memuat data.")
