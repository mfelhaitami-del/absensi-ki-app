import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image
from io import BytesIO

# --- 1. KONFIGURASI (PASTIKAN DIISI DENGAN BENAR) ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbw023Tt8XlEoU3dY174XUFUeBLepwSFCT-jzAnPf-CT4IIJRp0WbIdqnG1MZQ-Wg7Ct/exec"

st.set_page_config(page_title="Sistem Absensi Tim KI", layout="wide")

# --- 2. CUSTOM CSS TAMPILAN ---
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
        font-size: 38px; font-weight: 800; text-align: center; 
        color: #1e293b; margin-top: -50px;
    }
    .stTable { background-color: white; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNGSI JAM REAL-TIME (ANTAR-MUKA DINAMIS) ---
@st.fragment(run_every="1s")
def jam_sidebar():
    # Mengambil waktu WIB (UTC+7)
    waktu_skrg = datetime.datetime.now() + datetime.timedelta(hours=7)
    st.markdown(f"""
    <div class="sidebar-time-box">
        <span style="font-size: 14px;">📅 {waktu_skrg.strftime('%d %B %Y')}</span><br>
        <span style="font-size: 30px; color: #3b82f6; font-weight: bold;">{waktu_skrg.strftime('%H:%M:%S')}</span><br>
        <span style="font-weight: bold; letter-spacing: 2px;">WIB</span>
    </div>
    """, unsafe_allow_html=True)
    return waktu_skrg

# --- 4. SIDEBAR NAVIGASI ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
    st.markdown("### Dashboard Navigasi")
    menu = st.radio("Pilih Menu:", ["📍 Presensi Wajah", "📊 Rekap Absensi"])
    st.divider()
    waktu_aktif = jam_sidebar()

# --- 5. HALAMAN 1: PRESENSI ---
if menu == "📍 Presensi Wajah":
    st.markdown('<p class="hero-title">Absensi Tim KI Satker PPS Banten</p>', unsafe_allow_html=True)
    
    # Penentuan Status Sesi Berdasarkan Jam
    if 6 <= waktu_aktif.hour < 12:
        status_sesi = "MASUK"
    elif 13 <= waktu_aktif.hour < 23: # Diperlebar untuk testing
        status_sesi = "PULANG"
    else:
        status_sesi = "TUTUP"

    if status_sesi == "TUTUP":
        st.error(f"🚫 Maaf, Sesi Absensi sedang ditutup. (Waktu Sekarang: {waktu_aktif.strftime('%H:%M:%S')} WIB)")
    else:
        st.info(f"📍 Sesi Sekarang: **Absen {status_sesi}**")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            daftar_nama = [
                "Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", 
                "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", 
                "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"
            ]
            nama_user = st.selectbox("Pilih Nama Anda:", daftar_nama)
            st.warning("📸 Pastikan wajah terlihat jelas di kamera.")
            
        with col2:
            foto = st.camera_input("Ambil Foto Wajah")

        if st.button(f"🚀 KIRIM ABSENSI {status_sesi}", use_container_width=True):
            if foto and nama_user:
                with st.spinner("Sedang memproses foto dan mengirim data..."):
                    try:
                        # Step 1: Upload ke ImgBB
                        img_bytes = foto.getvalue()
                        res_img = requests.post(
                            f"https://api.imgbb.com/1/upload?key={API_IMGBB}",
                            files={"image": img_bytes}
                        ).json()
                        link_foto_raw = res_img["data"]["url"]

                        # Step 2: Kirim ke Google Sheets
                        payload = {
                            "nama": nama_user,
                            "tanggal": waktu_aktif.strftime("%Y-%m-%d"),
                            "jam": waktu_aktif.strftime("%H:%M:%S"),
                            "status": status_sesi,
                            "foto_link": link_foto_raw
                        }
                        res_sheets = requests.post(WEBAPP_URL, json=payload)

                        if res_sheets.status_code == 200:
                            st.success(f"✅ Berhasil! Absen {status_sesi} tercatat pada {payload['jam']} WIB.")
                            st.balloons()
                        else:
                            st.error("Gagal mengirim ke database Spreadsheet.")
                    except Exception as e:
                        st.error(f"Terjadi kesalahan teknis: {e}")
            else:
                st.warning("⚠️ Silakan ambil foto terlebih dahulu sebelum mengirim!")

# --- 6. HALAMAN 2: REKAP ---
else:
    st.markdown('<p class="hero-title">Laporan Kehadiran Bulanan</p>', unsafe_allow_html=True)
    
    bulan_list = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni", 
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    
    c1, c2 = st.columns(2)
    with c1:
        p_bulan = st.selectbox("Pilih Bulan:", bulan_list, index=waktu_aktif.month - 1)
    with c2:
        p_tahun = st.selectbox("Pilih Tahun:", [2025, 2026], index=1)

    if st.button("🔍 Tampilkan Data Rekap", use_container_width=True):
        nama_tab = f"{p_bulan} {p_tahun}"
        try:
            # Mengambil data dari Apps Script via GET
            res = requests.get(f"{WEBAPP_URL}?bulan={nama_tab}")
            data_json = res.json()
            
            if data_json:
                df = pd.DataFrame(data_json)
                
                # Memfilter hanya kolom utama agar tabel rapi
                kolom_tampil = ["Nama", "Tanggal", "Jam Masuk", "Jam Pulang"]
                # Cek apakah kolom tersedia di spreadsheet
                available_cols = [c for c in kolom_tampil if c in df.columns]
                df_final = df[available_cols]
                
                # Mengatur Nomor Urut mulai dari 1
                df_final.index = range(1, len(df_final) + 1)
                
                st.write(f"### 📋 Rekap Absensi: {nama_tab}")
                st.table(df_final)
            else:
                st.info(f"ℹ️ Belum ada data absensi untuk periode {nama_tab}.")
        except:
            st.error("❌ Gagal mengambil data. Pastikan URL Web App Apps Script sudah benar dan di-deploy sebagai 'Anyone'.")
