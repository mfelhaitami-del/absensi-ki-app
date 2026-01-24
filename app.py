import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image
from io import BytesIO

# --- KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0" # Ganti dengan API Key ImgBB Anda
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzJiIm08gnok9UCvDF329WB_xtchuJjuL7cnTONuB7_CnPyvprF5Po2gl9kenZ6eIeD/exec" # Ganti dengan URL dari langkah 1

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# --- FRAGMENT UNTUK JAM REAL-TIME ---
@st.fragment(run_every="1s")
def jam_sidebar():
    waktu_skrg = datetime.datetime.now() + datetime.timedelta(hours=7)
    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.1); padding:15px; border-radius:10px; text-align:center; border:1px solid #3b82f6;">
        <span style="color:white; font-size:14px;">{waktu_skrg.strftime('%d %B %Y')}</span><br>
        <span style="color:#3b82f6; font-size:28px; font-weight:bold;">{waktu_skrg.strftime('%H:%M:%S')}</span><br>
        <span style="color:white; font-weight:bold;">WIB</span>
    </div>
    """, unsafe_allow_html=True)
    return waktu_skrg

# --- MENU UTAMA ---
with st.sidebar:
    st.header("🏢 Dashboard KI")
    menu = st.radio("Navigasi", ["📍 Absensi", "📊 Rekap Absensi"])
    st.divider()
    waktu_aktif = jam_sidebar()

# --- LOGIKA HALAMAN ---
if menu == "📍 Absensi":
    st.title("Absensi Tim KI Satker PPS Banten")
    
    # Penentuan Sesi
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
                try:
                    # Upload Foto
                    files = {"image": foto.getvalue()}
                    img_res = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files=files).json()
                    link_foto = img_res["data"]["url"]
                    
                    # Kirim ke Sheets
                    payload = {
                        "nama": nama, "tanggal": waktu_aktif.strftime("%Y-%m-%d"),
                        "jam": waktu_aktif.strftime("%H:%M:%S"), "status": status_sesi, "foto_link": link_foto
                    }
                    requests.post(WEBAPP_URL, json=payload)
                    st.success(f"✅ Berhasil Absen {status_sesi}!")
                    st.balloons()
                except: st.error("Gagal mengirim data.")
            else: st.warning("⚠️ Foto dulu bos!")

else:
    st.title("Rekap Data Bulanan")
    bulan_list = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    c1, c2 = st.columns(2)
    with c1: b = st.selectbox("Bulan", bulan_list, index=waktu_aktif.month - 1)
    with c2: t = st.selectbox("Tahun", [2025, 2026], index=1)
    
    if st.button("🔍 Tampilkan Rekap"):
        res = requests.get(f"{WEBAPP_URL}?bulan={b} {t}").json()
        if res:
            df = pd.DataFrame(res)
            df_final = df[["Nama", "Tanggal", "Jam Masuk", "Jam Pulang"]]
            df_final.index = range(1, len(df_final) + 1) # No urut dari 1
            st.table(df_final)
        else: st.info("Belum ada data.")
