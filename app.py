import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image, ImageDraw, ImageFont
import io
import numpy as np
import time

# --- KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbPpLKx52ihMewXuriN7xb94BFuiIHkMYiFDeTrWNj8vSy7DbE2Oj530jq87M4yJtl9/exec"

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

# --- FUNGSI WATERMARK & KIRIM DATA ---
def kirim_ke_sheets(nama, status, foto, w_skrg):
    try:
        # 1. Buka Gambar & Anti-Mirror
        img = Image.open(foto).convert("RGB")
        img_array = np.array(img)
        img_flipped = np.flip(img_array, axis=1)
        img = Image.fromarray(img_flipped)
        
        # 2. Tambahkan Watermark (Nama, Jam, Hari Tanggal)
        draw = ImageDraw.Draw(img)
        
        # Pengaturan Teks
        hari_tgl = w_skrg.strftime("%A, %d %B %Y").replace("Monday", "Senin").replace("Tuesday", "Selasa").replace("Wednesday", "Rabu").replace("Thursday", "Kamis").replace("Friday", "Jumat").replace("Saturday", "Sabtu").replace("Sunday", "Minggu")
        jam_str = w_skrg.strftime("%H:%M:%S") + " WIB"
        text_watermark = f"{nama}\n{jam_str}\n{hari_tgl}"
        
        # Ukuran font dinamis berdasarkan lebar gambar (sekitar 3% dari lebar)
        font_size = int(img.width * 0.035)
        try:
            # Mencoba memuat font default Streamlit/Linux, jika gagal pakai default PIL
            font = ImageFont.load_default() 
        except:
            font = ImageFont.load_default()

        # Posisi teks (Pojok kiri bawah dengan margin)
        margin = 20
        # Menggunakan multiline_text untuk menangani baris baru (\n)
        # Menambahkan bayangan (shadow) hitam agar teks terbaca di background terang
        draw.multiline_text((margin+2, img.height - font_size*4 + 2), text_watermark, fill=(0, 0, 0), font=font, spacing=4)
        draw.multiline_text((margin, img.height - font_size*4), text_watermark, fill=(255, 255, 255), font=font, spacing=4)
        
        # 3. Simpan ke Buffer
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        
        # 4. Upload ke ImgBB
        r_img = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": buf.getvalue()}).json()
        link = r_img["data"]["url"]
        
        # 5. Kirim Payload ke Google Apps Script
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
        st.error(f"Gagal memproses gambar: {e}")
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
            with st.status("Sedang memproses watermark & mengirim data...", expanded=False) as s:
                sukses = kirim_ke_sheets(nama, status_sesi, foto, w_skrg)
                if sukses:
                    s.update(label="✅ Absen Berhasil Terkirim!", state="complete", expanded=False)
                    st.toast(f"Terima kasih {nama}, data sudah masuk.", icon='✅')
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
    # Menyesuaikan waktu ke WIB (UTC+7)
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
                df.insert(0, 'No', range(1, 1 + len(df)))
                
                st.dataframe(
                    df[['No', 'Nama', 'Tanggal', 'Jam Masuk', 'Jam Pulang']], 
                    hide_index=True, 
                    use_container_width=True,
                    column_config={
                        "No": st.column_config.Column("No", width="small"),
                        "Nama": st.column_config.Column("Nama", width="medium"),
                    }
                )
            else:
                st.info(f"Data absensi untuk periode {b} {t} belum tersedia.")
        except:
            st.error("Gagal mengambil data dari Spreadsheet.")
