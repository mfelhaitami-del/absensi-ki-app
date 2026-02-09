import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. KONFIGURASI ---
# Pastikan API Key ImgBB dan URL Deployment Apps Script Anda sudah benar
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbw3AtbN2Znxq1XJDEYHkgQqC-G8SU_7RcwptjmzzS9dXNyd5iK8d-Kk3cKaODfl_FrC/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# --- 2. CUSTOM CSS (BACKGROUND & GLASSMORPHISM) ---
# Menggunakan CSS murni untuk menghindari bentrok kurung kurawal f-string
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Poppins', sans-serif; 
    }

    /* BACKGROUND GAMBAR UTAMA */
    .stApp {
        background: linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.5)), 
                    url("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Logo_PU_%28RGB%29.jpg/960px-Logo_PU_%28RGB%29.jpg");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] { 
        background-color: rgba(15, 23, 42, 0.9) !important; 
        backdrop-filter: blur(10px);
    }
    [data-testid="stSidebar"] * { color: white !important; }
    
    /* Box Jam Sidebar */
    .sidebar-time-box { 
        background-color: rgba(255,255,255,0.1); 
        padding: 15px; border-radius: 12px; text-align: center; 
        border: 1px solid #3b82f6; margin-bottom: 20px;
    }

    /* Judul Halaman */
    .hero-title { 
        font-size: 32px; font-weight: 800; text-align: center; 
        color: #ffffff; margin-top: -30px; margin-bottom: 30px;
        text-shadow: 2px 4px 8px rgba(0,0,0,0.8);
    }

    /* Styling Tabel Rekap (Minimalis & Transparan) */
    [data-testid="stDataFrame"] {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: none !important;
        border-radius: 10px;
    }
    
    /* Menghilangkan padding berlebih */
    .block-container {
        padding-top: 3rem;
        padding-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNGSI JAM REAL-TIME (WIB) ---
@st.fragment(run_every="1s")
def jam_sidebar():
    # Menghitung WIB (UTC+7)
    waktu_skrg = datetime.datetime.now() + datetime.timedelta(hours=7)
    st.markdown(f"""
    <div class="sidebar-time-box">
        <span style="font-size: 14px;">{waktu_skrg.strftime('%d %B %Y')}</span><br>
        <span style="font-size: 28px; color: #3b82f6; font-weight: bold;">{waktu_skrg.strftime('%H:%M:%S')}</span><br>
        <b>WIB</b>
    </div>
    """, unsafe_allow_html=True)
    return waktu_skrg

# --- 4. NAVIGASI SIDEBAR (DROPDOWN) ---
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
    
    # Logika Sesi Otomatis
    status_sesi = "TUTUP"
    if 6 <= waktu_aktif.hour < 12: status_sesi = "MASUK"
    elif 12 <= waktu_aktif.hour < 23: status_sesi = "PULANG"
    
    if status_sesi == "TUTUP":
        st.error(f"🚫 Sesi Absensi Tutup. (Sekarang: {waktu_aktif.strftime('%H:%M:%S')} WIB)")
    else:
        st.info(f"📍 Sesi Sekarang: **Absen {status_sesi}**")
        nama = st.selectbox("Pilih Nama:", [
            "Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", 
            "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", 
            "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"
        ])
        foto = st.camera_input("Ambil Foto Wajah")
        
        if st.button("KIRIM DATA ABSENSI", use_container_width=True):
            if foto:
                with st.spinner("Mengupload foto & menyinkronkan data..."):
                    try:
                        # 1. Upload ke ImgBB
                        files = {"image": foto.getvalue()}
                        res_img = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files=files).json()
                        link_foto = res_img["data"]["url"]
                        
                        # 2. Payload Data
                        payload = {
                            "nama": nama, 
                            "tanggal": waktu_aktif.strftime("%Y-%m-%d"), 
                            "jam": waktu_aktif.strftime("%H:%M:%S"), 
                            "status": status_sesi, 
                            "foto_link": link_foto
                        }
                        
                        # 3. Kirim ke Google Apps Script
                        # Gunakan timeout agar tidak menunggu terlalu lama jika koneksi drop
                        response = requests.post(WEBAPP_URL, json=payload, timeout=15)
                        
                        if response.status_code == 200:
                            st.success(f"✅ Berhasil! Absen {status_sesi} Anda telah tercatat.")
                        else:
                            st.error(f"Gagal mengirim (Status: {response.status_code}). Periksa Deployment Apps Script.")
                            
                    except Exception as e:
                        st.error(f"⚠️ Kesalahan Koneksi: Pastikan URL Apps Script benar dan internet stabil.")
            else:
                st.warning("⚠️ Silakan ambil foto wajah terlebih dahulu!")

# --- 6. HALAMAN 2: REKAP ABSENSI (FULL SIZE & DOWNLOADABLE) ---
else:
    st.markdown('<p class="hero-title">📊 Rekap Kehadiran Bulanan</p>', unsafe_allow_html=True)
    
    bulan_indo = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    
    # Baris Filter
    c1, c2 = st.columns(2)
    with c1:
        p_bulan = st.selectbox("Pilih Bulan", bulan_indo, index=waktu_aktif.month - 1)
    with c2:
        p_tahun = st.selectbox("Pilih Tahun", [2025, 2026], index=1)
    
    if st.button("🔍 Tampilkan Rekap Data", use_container_width=True):
        try:
            # Mengambil data menggunakan parameter URL
            fetch_url = f"{WEBAPP_URL}?bulan={p_bulan} {p_tahun}"
            res = requests.get(fetch_url, timeout=15).json()
            
            if res:
                df = pd.DataFrame(res)
                # Filter hanya kolom yang diperlukan
                df_tampil = df[["Nama", "Tanggal", "Jam Masuk", "Jam Pulang"]]
                # Set nomor urut mulai dari 1
                df_tampil.index = range(1, len(df_tampil) + 1)
                
                st.write(f"### 📋 Laporan Periode: {p_bulan} {p_tahun}")
                
                # Tabel Full Size & Bisa Download
                st.dataframe(
                    df_tampil, 
                    use_container_width=True, 
                    height=500
                )
                st.caption("📥 **Info:** Klik ikon di pojok kanan atas tabel untuk mendownload data.")
            else:
                st.info(f"ℹ️ Belum ada data absensi untuk bulan {p_bulan} {p_tahun}.")
        except Exception as e:
            st.error("❌ Gagal memuat data. Periksa apakah nama sheet di Google Sheets sudah benar (Contoh: Februari 2026).")
