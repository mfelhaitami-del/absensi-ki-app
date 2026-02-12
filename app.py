import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image
import io
import numpy as np
import time

# --- KONFIGURASI ---
# Ganti dengan API Key ImgBB Anda jika berbeda
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
# Pastikan URL ini adalah URL /exec dari deployment Apps Script terbaru Anda
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbx3tEh9mSuiK4viX-GZZzEPoonb1Oi_j9fVrdNqlHXE5NjEccoBlar0ej5jodm6xbbv/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# --- CSS: BACKGROUND & KAMERA ANTI-MIRROR ---
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

# --- FUNGSI PROSES KIRIM DATA ---
def kirim_ke_sheets(nama, status, foto, w_skrg):
    try:
        # Proses Image (Anti-Mirror)
        img = Image.open(foto).convert("RGB")
        f_img = Image.fromarray(np.flip(np.array(img), axis=1))
        buf = io.BytesIO()
        f_img.save(buf, format="JPEG")
        
        # Upload ke ImgBB
        r_img = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": buf.getvalue()}).json()
        link = r_img["data"]["url"]
        
        # Kirim Payload ke Google Apps Script
        payload = {
            "nama": nama, 
            "tanggal": w_skrg.strftime("%Y-%m-%d"), 
            "jam": w_skrg.strftime("%H:%M:%S"), 
            "status": status, 
            "foto_link": link
        }
        response = requests.post(WEBAPP_URL, json=payload, timeout=20)
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

# --- POP-UP DIALOG KONFIRMASI ---
@st.dialog("Konfirmasi Absensi")
def konfirmasi_dialog(nama, status_sesi, foto, w_skrg):
    st.warning("⚠️ Pastikan nama sudah benar sesuai nama anda!")
    st.write(f"Nama Terpilih: **{nama}**")
    st.write(f"Sesi: **{status_sesi}**")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Ya, Sudah Benar", use_container_width=True, type="primary"):
            # Menggunakan st.status untuk indikator progres yang jelas
            with st.status("Sedang mengirim data absensi...", expanded=False) as s:
                sukses = kirim_ke_sheets(nama, status_sesi, foto, w_skrg)
                if sukses:
                    s.update(label="✅ Absen Berhasil Terkirim!", state="complete", expanded=False)
                    st.toast(f"Terima kasih {nama}, data sudah masuk.", icon='✅')
                    # Jeda 3 detik agar user bisa melihat notifikasi sukses sebelum rerun
                    time.sleep(3)
                    st.rerun()
                else:
                    s.update(label="❌ Gagal mengirim data!", state="error")
                    st.error("Terjadi kendala koneksi ke server. Silakan coba lagi.")
                    
    with col2:
        if st.button("Tidak, Ganti Nama", use_container_width=True):
            st.rerun()

# --- JAM REAL-TIME DI SIDEBAR ---
@st.fragment(run_every="1s")
def jam_sidebar():
    w = datetime.datetime.now() + datetime.timedelta(hours=7)
    st.markdown(f'''<div class="sidebar-box"><span style="color:white">{w.strftime("%d %B %Y")}</span><br>
    <span style="font-size:24px; color:#3b82f6; font-weight:bold;">{w.strftime("%H:%M:%S")}</span><br>
    <small style="color:white">WIB</small></div>''', unsafe_allow_html=True)
    return w

# --- STRUKTUR SIDEBAR ---
with st.sidebar:
    st.header("🏢 MENU UTAMA")
    menu = st.selectbox("Layanan:", ["📍 Absensi", "📊 Rekap Absensi"])
    st.divider()
    w_skrg = jam_sidebar()

# --- HALAMAN 📍 ABSENSI ---
if menu == "📍 Absensi":
    st.markdown("<h2 style='text-align:center; color:white;'>Absensi Tim KI Satker PPS Banten</h2>", unsafe_allow_html=True)
    
    # Logika Jam Sesi (Masuk: 06-12, Pulang: 12-23)
    status_sesi = "MASUK" if 6 <= w_skrg.hour < 12 else "PULANG" if 12 <= w_skrg.hour < 23 else "TUTUP"
    
    if status_sesi == "TUTUP":
        st.error("🚫 Sesi Absensi sedang ditutup (Aktif 06:00 - 23:00 WIB).")
    else:
        st.info(f"Sesi Aktif saat ini: **{status_sesi}**")
        nama = st.selectbox("Pilih Nama Anda:", [
            "Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", 
            "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", 
            "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"
        ])
        
        foto = st.camera_input("Ambil Foto Wajah")
        
        if st.button("KIRIM DATA ABSENSI", use_container_width=True):
            if foto:
                # Memanggil dialog konfirmasi pop-up
                konfirmasi_dialog(nama, status_sesi, foto, w_skrg)
            else:
                st.warning("📸 Silakan ambil foto terlebih dahulu!")

# --- HALAMAN 📊 REKAP ABSENSI ---
else:
    st.markdown("<h2 style='text-align:center; color:white;'>📊 Rekap Absensi Bulanan</h2>", unsafe_allow_html=True)
    list_b = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    
    c1, c2 = st.columns(2)
    b = c1.selectbox("Pilih Bulan:", list_b, index=w_skrg.month - 1)
    t = c2.selectbox("Pilih Tahun:", [2025, 2026, 2027], index=1)

    if st.button("🔍 Tampilkan Data Rekap", use_container_width=True):
        try:
            res = requests.get(f"{WEBAPP_URL}?bulan={b} {t}", timeout=25).json()
            if res:
                df = pd.DataFrame(res)
                # Membuat nomor urut mulai dari 1
                df.insert(0, 'No', range(1, 1 + len(df)))
                
                # --- PENGATURAN LEBAR KOLOM ---
                st.dataframe(
                    df[['No', 'Nama', 'Tanggal', 'Jam Masuk', 'Jam Pulang']], 
                    hide_index=True, 
                    use_container_width=True,
                    column_config={
                        "No": st.column_config.Column(
                            "No",
                            width="small",  # Mengecilkan ukuran kolom No
                        ),
                        "Nama": st.column_config.Column(
                            "Nama",
                            width="medium",  # Melebarkan kolom Nama agar seimbang
                        ),
                        "Tanggal": st.column_config.Column(width="medium"),
                        "Jam Masuk": st.column_config.Column(width="medium"),
                        "Jam Pulang": st.column_config.Column(width="medium"),
                    }
                )
            else:
                st.info(f"Data absensi untuk periode {b} {t} belum tersedia.")
        except:
            st.error("Gagal mengambil data dari Spreadsheet.")
