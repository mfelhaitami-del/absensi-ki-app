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

# --- 2. CUSTOM CSS (FIX TAMPILAN & WARNA) ---
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
        color: #ffffff; margin-top: -30px; margin-bottom: 20px;
    }

    /* Styling Dataframe agar kontras */
    [data-testid="stDataFrame"] {
        background-color: #f8fafc;
        padding: 10px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNGSI JAM OTOMATIS ---
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

# --- 4. NAVIGASI SIDEBAR ---
with st.sidebar:
    st.markdown("## 🏢 Dashboard KI")
    menu = st.radio("Navigasi Menu", ["📍 Presensi Wajah", "📊 Rekap Absensi"])
    st.divider()
    waktu_aktif = jam_sidebar()

# --- 5. HALAMAN 1: PRESENSI ---
if menu == "📍 Presensi Wajah":
    st.markdown('<p class="hero-title">Absensi Tim KI Satker PPS Banten</p>', unsafe_allow_html=True)
    
    # Logika Sesi Absen
    status_sesi = "TUTUP"
    if 6 <= waktu_aktif.hour < 12: status_sesi = "MASUK"
    elif 13 <= waktu_aktif.hour < 23: status_sesi = "PULANG"
    
    if status_sesi == "TUTUP":
        st.error(f"🚫 Sesi Absensi Tutup. (Waktu: {waktu_aktif.strftime('%H:%M:%S')} WIB)")
    else:
        st.info(f"📍 Sesi: **Absen {status_sesi}**")
        nama = st.selectbox("Pilih Nama:", ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"])
        foto = st.camera_input("Ambil Foto Wajah")
        
        if st.button(f"🚀 Kirim Absen {status_sesi}", use_container_width=True):
            if foto:
                with st.spinner("Mengirim data..."):
                    try:
                        # Upload ImgBB
                        res_img = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": foto.getvalue()}).json()
                        link_foto = res_img["data"]["url"]
                        
                        # Kirim Google Sheets
                        payload = {
                            "nama": nama, "tanggal": waktu_aktif.strftime("%Y-%m-%d"),
                            "jam": waktu_aktif.strftime("%H:%M:%S"), "status": status_sesi, "foto_link": link_foto
                        }
                        requests.post(WEBAPP_URL, json=payload)
                        st.success("✅ Berhasil Terkirim!")
                        st.balloons()
                    except: st.error("Gagal mengirim.")
            else: st.warning("⚠️ Foto belum diambil.")

# --- 6. HALAMAN 2: REKAP (SIMPEL, FULL SIZE, DOWNLOADABLE) ---
else:
    st.markdown('<p class="hero-title">📊 Rekap Data Kehadiran</p>', unsafe_allow_html=True)
    
    bulan_indo = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    c1, c2 = st.columns(2)
    with c1: b = st.selectbox("Pilih Bulan", bulan_indo, index=waktu_aktif.month - 1)
    with c2: t = st.selectbox("Pilih Tahun", [2025, 2026], index=1)
    
    if st.button("🔍 Tampilkan Data Laporan", use_container_width=True):
        try:
            res = requests.get(f"{WEBAPP_URL}?bulan={b} {t}").json()
            if res:
                df = pd.DataFrame(res)
                
                # Filter Kolom
                df_final = df[["Nama", "Tanggal", "Jam Masuk", "Jam Pulang"]]
                
                # Mengatur Nomor Urut mulai dari 1
                df_final.index = range(1, len(df_final) + 1)
                
                st.write(f"### 📋 Laporan: {b} {t}")
                
                # MENGGUNAKAN DATAFRAME AGAR BISA DOWNLOAD & FULL SIZE
                st.dataframe(
                    df_final, 
                    use_container_width=True, # Full Size
                    height=500
                )
                
                st.caption("💡 Klik ikon download di pojok kanan atas tabel untuk mengunduh file CSV.")
            else:
                st.info("Belum ada data untuk periode ini.")
        except:
            st.error("Gagal mengambil data dari server.")
