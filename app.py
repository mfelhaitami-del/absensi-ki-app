import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image
from io import BytesIO

# --- KONFIGURASI (WAJIB DIISI) ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0" 
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzkTbuybyzZror68RNfVguRLXONUStkPi9VL2CpZzH31DorBS2iTgN83o73KhksS7M/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# --- CSS TAMPILAN ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; }
    .sidebar-time-box { 
        background-color: rgba(255,255,255,0.1); 
        padding: 15px; border-radius: 12px; text-align: center; 
        color: white; border: 1px solid #3b82f6;
    }
    .hero-title { font-size: 35px; font-weight: 800; text-align: center; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI JAM OTOMATIS (Fragment) ---
@st.fragment(run_every="1s")
def jam_sidebar():
    # Waktu sekarang Indonesia (WIB = UTC+7)
    waktu_skrg = datetime.datetime.now() + datetime.timedelta(hours=7)
    st.markdown(f"""
    <div class="sidebar-time-box">
        <span style="font-size: 14px;">{waktu_skrg.strftime('%d %B %Y')}</span><br>
        <span style="font-size: 28px; color: #3b82f6; font-weight: bold;">{waktu_skrg.strftime('%H:%M:%S')}</span><br>
        <span style="font-weight: bold;">WIB</span>
    </div>
    """, unsafe_allow_html=True)
    return waktu_skrg

# --- MENU SIDEBAR ---
with st.sidebar:
    st.header("🏢 Dashboard KI")
    menu = st.radio("Navigasi", ["📍 Absensi", "📊 Rekap Absensi"])
    st.divider()
    waktu_aktif = jam_sidebar()

# --- HALAMAN 1: ABSENSI ---
if menu == "📍 Absensi":
    st.markdown('<p class="hero-title">Absensi Tim KI Satker PPS Banten</p>', unsafe_allow_html=True)
    
    # Logika Sesi
    status_sesi = "TUTUP"
    if 6 <= waktu_aktif.hour < 12: status_sesi = "MASUK"
    elif 13 <= waktu_aktif.hour < 23: status_sesi = "PULANG"
    
    if status_sesi == "TUTUP":
        st.error(f"🚫 Sesi Absensi Tutup. (Sekarang: {waktu_aktif.strftime('%H:%M:%S')} WIB)")
    else:
        st.info(f"📍 Sesi: **Absen {status_sesi}**")
        nama = st.selectbox("Pilih Nama:", ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"])
        foto = st.camera_input("Ambil Foto Wajah")
        
        if st.button(f"🚀 Kirim Absen {status_sesi}"):
            if foto:
                with st.spinner("Mengupload Foto & Data..."):
                    try:
                        # 1. Upload Foto ke ImgBB
                        files = {"image": foto.getvalue()}
                        img_res = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files=files).json()
                        link_foto = img_res["data"]["url"]
                        
                        # 2. Kirim Data ke Google Sheets
                        payload = {
                            "nama": nama, 
                            "tanggal": waktu_aktif.strftime("%Y-%m-%d"),
                            "jam": waktu_aktif.strftime("%H:%M:%S"), 
                            "status": status_sesi, 
                            "foto_link": link_foto
                        }
                        res_sheets = requests.post(WEBAPP_URL, json=payload)
                        
                        if res_sheets.status_code == 200:
                            st.success(f"✅ Berhasil! Data & Foto masuk ke Spreadsheet.")
                            st.balloons()
                        else:
                            st.error("Gagal terhubung ke Database.")
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.warning("⚠️ Ambil foto wajah terlebih dahulu!")

# --- HALAMAN 2: REKAP ---
else:
    st.markdown('<p class="hero-title">Rekap Data Bulanan</p>', unsafe_allow_html=True)
    bulan_list = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    
    c1, c2 = st.columns(2)
    with c1: b = st.selectbox("Pilih Bulan", bulan_list, index=waktu_aktif.month - 1)
    with c2: t = st.selectbox("Pilih Tahun", [2025, 2026], index=1)
    
    if st.button("🔍 Tampilkan Rekap"):
        with st.spinner("Memuat data..."):
            try:
                res = requests.get(f"{WEBAPP_URL}?bulan={b} {t}").json()
                if res:
                    df = pd.DataFrame(res)
                    # Ambil kolom yang dibutuhkan saja (Tanpa Kolom Foto)
                    df_final = df[["Nama", "Tanggal", "Jam Masuk", "Jam Pulang"]]
                    # Nomor urut mulai dari 1
                    df_final.index = range(1, len(df_final) + 1)
                    
                    st.write(f"### 📋 Laporan: {b} {t}")
                    st.table(df_final)
                else:
                    st.info(f"Belum ada data untuk periode {b} {t}")
            except:
                st.error("Gagal mengambil data. Pastikan nama sheet di Spreadsheet sudah benar.")
