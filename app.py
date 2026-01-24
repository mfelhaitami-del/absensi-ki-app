import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image
from io import BytesIO

# --- 1. KONFIGURASI (PASTIKAN DIISI) ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwKEM1F-kthxUFjIt_qc11U-98NEPLqD4g7nyl7TbHUA7H3QLSjchYC8U8bxSOxtuxM/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# --- 2. CUSTOM CSS (WARNA KONTRAS & TAMPILAN BERSIH) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] { background-color: #0f172a !important; }
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
    }

    /* Styling Tabel Rekap agar Kontras */
    [data-testid="stDataFrame"] {
        background-color: #f8fafc;
        padding: 5px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
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

# --- 4. NAVIGASI SIDEBAR ---
with st.sidebar:
    st.markdown("### 🏢 MENU UTAMA")
    menu = st.radio("Pilih Menu:", ["📍 Presensi Wajah", "📊 Rekap Absensi"])
    st.divider()
    waktu_aktif = jam_sidebar()

# --- 5. HALAMAN 1: PRESENSI ---
if menu == "📍 Presensi Wajah":
    st.markdown('<p class="hero-title">Absensi Tim KI Satker PPS Banten</p>', unsafe_allow_html=True)
    
    # Penentuan Sesi Absen
    status_sesi = "TUTUP"
    if 6 <= waktu_aktif.hour < 12: status_sesi = "MASUK"
    elif 13 <= waktu_aktif.hour < 23: status_sesi = "PULANG"
    
    if status_sesi == "TUTUP":
        st.error(f"🚫 Sesi Absensi Tutup. (Sekarang: {waktu_aktif.strftime('%H:%M:%S')} WIB)")
    else:
        st.info(f"📍 Sesi Sekarang: **Absen {status_sesi}**")
        nama = st.selectbox("Pilih Nama:", ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"])
        foto = st.camera_input("Ambil Foto Wajah")
        
        if st.button(f"🚀 KIRIM DATA ABSENSI", use_container_width=True):
            if foto:
                with st.spinner("Mengupload foto & menyinkronkan data..."):
                    try:
                        # 1. Upload ke ImgBB
                        res_img = requests.post(
                            f"https://api.imgbb.com/1/upload?key={API_IMGBB}", 
                            files={"image": foto.getvalue()}
                        ).json()
                        link_foto = res_img["data"]["url"]
                        
                        # 2. Kirim ke Google Sheets
                        payload = {
                            "nama": nama, "tanggal": waktu_aktif.strftime("%Y-%m-%d"),
                            "jam": waktu_aktif.strftime("%H:%M:%S"), "status": status_sesi, 
                            "foto_link": link_foto
                        }
                        requests.post(WEBAPP_URL, json=payload)
                        st.success(f"✅ Berhasil! Absen {status_sesi} tercatat.")
                        st.balloons()
                    except:
                        st.error("Gagal mengirim data. Cek koneksi atau URL API.")
            else:
                st.warning("⚠️ Silakan ambil foto wajah terlebih dahulu!")

# --- 6. HALAMAN 2: REKAP (FULL SIZE & DOWNLOADABLE) ---
else:
    st.markdown('<p class="hero-title">📊 Rekap Kehadiran Bulanan</p>', unsafe_allow_html=True)
    
    bulan_indo = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    
    # Kontrol Filter
    c1, c2 = st.columns(2)
    with c1:
        p_bulan = st.selectbox("Pilih Bulan", bulan_indo, index=waktu_aktif.month - 1)
    with c2:
        p_tahun = st.selectbox("Pilih Tahun", [2025, 2026], index=1)
    
    if st.button("🔍 Tampilkan Rekap Data", use_container_width=True):
        try:
            res = requests.get(f"{WEBAPP_URL}?bulan={p_bulan} {p_tahun}").json()
            if res:
                df = pd.DataFrame(res)
                
                # Hanya menampilkan kolom data utama
                df_tampil = df[["Nama", "Tanggal", "Jam Masuk", "Jam Pulang"]]
                
                # Mengatur Nomor Urut mulai dari 1
                df_tampil.index = range(1, len(df_tampil) + 1)
                
                st.write(f"### 📋 Laporan: {p_bulan} {p_tahun}")
                
                # TAMPILAN FULL SIZE DENGAN FITUR DOWNLOAD
                st.dataframe(
                    df_tampil, 
                    use_container_width=True, # Tabel Full Size
                    height=500                # Tinggi area scroll
                )
                
                st.caption("📥 **Informasi:** Klik ikon unduh di pojok kanan atas tabel untuk mendownload file CSV.")
            else:
                st.info(f"Belum ada data absensi untuk bulan {p_bulan} {p_tahun}.")
        except:
            st.error("Gagal memuat data dari Spreadsheet.")
