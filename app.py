import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image
import io
import numpy as np

# --- KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbx3tEh9mSuiK4viX-GZZzEPoonb1Oi_j9fVrdNqlHXE5NjEccoBlar0ej5jodm6xbbv/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# CSS untuk Background & Kamera Anti-Mirror
st.markdown("""
    <style>
    [data-testid="stCameraInput"] video, [data-testid="stCameraInput"] img { transform: scaleX(-1); }
    .stApp {
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
        url("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Logo_PU_%28RGB%29.jpg/960px-Logo_PU_%28RGB%29.jpg");
        background-size: cover; background-attachment: fixed;
    }
    .sidebar-box { background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #3b82f6; }
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI KIRIM DATA ---
def kirim_ke_sheets(nama, status, foto, w_skrg):
    try:
        img = Image.open(foto).convert("RGB")
        f_img = Image.fromarray(np.flip(np.array(img), axis=1))
        buf = io.BytesIO()
        f_img.save(buf, format="JPEG")
        
        # Upload ke ImgBB
        r_img = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": buf.getvalue()}).json()
        link = r_img["data"]["url"]
        
        # Kirim Payload
        payload = {
            "nama": nama, 
            "tanggal": w_skrg.strftime("%Y-%m-%d"), 
            "jam": w_skrg.strftime("%H:%M:%S"), 
            "status": status, 
            "foto_link": link
        }
        requests.post(WEBAPP_URL, json=payload, timeout=20)
        return True
    except:
        return False

# --- POP-UP KONFIRMASI ---
@st.dialog("Konfirmasi Absensi")
def konfirmasi_dialog(nama, status, foto, w_skrg):
    st.warning("⚠️ Pastikan nama sudah benar sesuai nama anda!")
    st.write(f"Nama Terpilih: **{nama}**")
    st.write(f"Sesi: **{status}**")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Ya, Sudah Benar", use_container_width=True, type="primary"):
            with st.spinner("Sedang mengirim..."):
                sukses = kirim_ke_sheets(nama, status, foto, w_skrg)
                if sukses:
                    st.success("✅ Berhasil dikirim!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Gagal mengirim data.")
    with col2:
        if st.button("Tidak, Ganti Nama", use_container_width=True):
            st.rerun()

# --- JAM SIDEBAR ---
@st.fragment(run_every="1s")
def jam_sidebar():
    w = datetime.datetime.now() + datetime.timedelta(hours=7)
    st.markdown(f'''<div class="sidebar-box"><span style="color:white">{w.strftime("%d %B %Y")}</span><br>
    <span style="font-size:24px; color:#3b82f6; font-weight:bold;">{w.strftime("%H:%M:%S")}</span><br>
    <small style="color:white">WIB</small></div>''', unsafe_allow_html=True)
    return w

with st.sidebar:
    st.header("🏢 MENU UTAMA")
    menu = st.selectbox("Layanan:", ["📍 Absensi", "📊 Rekap Absensi"])
    st.divider()
    w_skrg = jam_sidebar()

# --- LOGIKA HALAMAN ---
if menu == "📍 Absensi":
    st.markdown("<h2 style='text-align:center; color:white;'>Absensi Tim KI Satker PPS Banten</h2>", unsafe_allow_html=True)
    status_sesi = "MASUK" if 6 <= w_skrg.hour < 12 else "PULANG" if 12 <= w_skrg.hour < 23 else "TUTUP"
    
    if status_sesi == "TUTUP":
        st.error("🚫 Sesi Absensi sedang ditutup.")
    else:
        nama = st.selectbox("Pilih Nama:", ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"])
        foto = st.camera_input("Ambil Foto Wajah")
        
        if st.button("KIRIM DATA ABSENSI", use_container_width=True):
            if foto:
                # Memanggil Dialog Pop-up
                konfirmasi_dialog(nama, status_sesi, foto, w_skrg)
            else:
                st.warning("📸 Silakan ambil foto terlebih dahulu!")

else:
    st.markdown("<h2 style='text-align:center; color:white;'>📊 Rekap Absensi Bulanan</h2>", unsafe_allow_html=True)
    list_b = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    c1, c2 = st.columns(2)
    b = c1.selectbox("Bulan:", list_b, index=w_skrg.month - 1)
    t = c2.selectbox("Tahun:", [2025, 2026, 2027], index=1)

    if st.button("🔍 Tampilkan Data Rekap", use_container_width=True):
        try:
            res = requests.get(f"{WEBAPP_URL}?bulan={b} {t}", timeout=25).json()
            if res:
                df = pd.DataFrame(res)
                df.insert(0, 'No', range(1, 1 + len(df)))
                st.table(df[['No', 'Nama', 'Tanggal', 'Jam Masuk', 'Jam Pulang']])
            else:
                st.info(f"Belum ada data.")
        except:
            st.error("Gagal memuat data rekap.")
