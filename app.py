import streamlit as st
import pandas as pd
import datetime
import requests
import time
from PIL import Image
from io import BytesIO

# --- KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzxgHFaJttC3Wnrw0-4XZdPt7n24QeB-Z-pQWv4bhO9CzVDLhyIqj7-DaWLMFxO2VVL/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# --- CSS TAMPILAN ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; }
    .sidebar-time-box { background-color: rgba(255,255,255,0.1); padding: 15px; border-radius: 12px; text-align: center; color: white; border: 1px solid rgba(255,255,255,0.2); }
    .hero-title { font-size: 35px; font-weight: 800; text-align: center; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI JAM BERJALAN (AUTOMATIC REFRESH) ---
@st.fragment(run_every="1s")
def jam_sidebar():
    waktu_skrg = datetime.datetime.now() + datetime.timedelta(hours=7)
    st.markdown(f"""
    <div class="sidebar-time-box">
        📅 <b>{waktu_skrg.strftime('%d %B %Y')}</b><br>
        <span style="font-size: 26px; color: #3b82f6;">⏰ <b>{waktu_skrg.strftime('%H:%M:%S')}</b></span><br>
        <b>WIB</b>
    </div>
    """, unsafe_allow_html=True)
    return waktu_skrg

# --- HALAMAN 1: ABSENSI ---
def halaman_presensi(waktu_aktif):
    st.markdown('<p class="hero-title">Absensi Tim KI Satker PPS Banten</p>', unsafe_allow_html=True)
    
    # Penentuan Sesi
    status_absen = "TUTUP"
    if 6 <= waktu_aktif.hour < 12: status_absen = "MASUK"
    elif 13 <= waktu_aktif.hour < 23: status_absen = "PULANG"
    
    if status_absen == "TUTUP":
        st.error(f"🚫 Sesi absensi tutup. (Sekarang: {waktu_aktif.strftime('%H:%M:%S')} WIB)")
    else:
        daftar_nama = ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"]
        nama_lengkap = st.selectbox("Pilih nama Anda:", daftar_nama)
        st.info(f"📍 Sesi: **Absen {status_absen}**")
        foto = st.camera_input("Ambil foto wajah")

        if st.button(f"🚀 Kirim Absensi {status_absen}"):
            if foto:
                with st.spinner("Sedang mengirim..."):
                    try:
                        img = Image.open(foto)
                        buf = BytesIO()
                        img.save(buf, format="JPEG")
                        files = {"image": buf.getvalue()}
                        resp = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files=files)
                        link_foto = resp.json()["data"]["url"]
                        
                        payload = {
                            "nama": nama_lengkap, 
                            "tanggal": waktu_aktif.strftime("%Y-%m-%d"), 
                            "jam": waktu_aktif.strftime("%H:%M:%S"), 
                            "status": status_absen, 
                            "foto_link": link_foto
                        }
                        requests.post(WEBAPP_URL, json=payload)
                        st.success(f"🎉 Berhasil! Tercatat jam {waktu_aktif.strftime('%H:%M:%S')} WIB.")
                    except:
                        st.error("Gagal mengirim data.")
            else:
                st.warning("⚠️ Ambil foto dulu!")

# --- HALAMAN 2: REKAP ---
def halaman_rekap(waktu_aktif):
    st.markdown('<p class="hero-title">Rekap Data Bulanan</p>', unsafe_allow_html=True)
    bulan_indo = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    
    c1, c2 = st.columns(2)
    with c1: p_bulan = st.selectbox("Bulan", bulan_indo, index=waktu_aktif.month - 1)
    with c2: p_tahun = st.selectbox("Tahun", [2025, 2026], index=1)
    
    if st.button("🔍 Tampilkan Data Laporan"):
        nama_tab = f"{p_bulan} {p_tahun}"
        try:
            res = requests.get(f"{WEBAPP_URL}?bulan={nama_tab}")
            data_json = res.json()
            if data_json:
                df = pd.DataFrame(data_json)
                kolom_show = ["Nama", "Tanggal", "Jam Masuk", "Jam Pulang"]
                df_final = df[[c for c in kolom_show if c in df.columns]]
                
                # Nomor urut mulai dari 1
                df_final.index = range(1, len(df_final) + 1)
                
                st.write(f"### 📋 Laporan: {nama_tab}")
                st.table(df_final)
            else:
                st.info(f"Data di sheet '{nama_tab}' masih kosong.")
        except:
            st.error("Gagal mengambil data.")

# --- SIDEBAR & NAVIGASI ---
with st.sidebar:
    st.markdown("## 🏢 Dashboard KI")
    menu = st.selectbox("Navigasi", ["📍 Absensi", "📊 Rekap Absensi"])
    st.divider()
    # Panggil fungsi jam di sini
    waktu_skrg = jam_sidebar()

# --- JALANKAN HALAMAN ---
if menu == "📍 Absensi":
    halaman_presensi(waktu_skrg)
else:
    halaman_rekap(waktu_skrg)
