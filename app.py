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
    /* Kamera di layar tidak mirror (tampilan) */
    [data-testid="stCameraInput"] video, [data-testid="stCameraInput"] img { transform: scaleX(-1); }
    .stApp {
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
        url("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Logo_PU_%28RGB%29.jpg/960px-Logo_PU_%28RGB%29.jpg");
        background-size: cover; background-attachment: fixed;
    }
    .sidebar-box { 
        background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #3b82f6; 
        color: white; /* Pastikan teks di sidebar terlihat */
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI WATERMARK & KIRIM DATA ---
def kirim_ke_sheets(nama, status, foto, w_skrg):
    try:
        # 1. Buka Gambar & Anti-Mirror
        img = Image.open(foto).convert("RGB")
        img_array = np.array(img)
        img_flipped = np.flip(img_array, axis=1) # Membalik secara horizontal
        img = Image.fromarray(img_flipped)
        
        # 2. Tambahkan Watermark (Nama, Jam, Hari Tanggal)
        draw = ImageDraw.Draw(img)
        
        # Konversi Hari ke Bahasa Indonesia
        hari_map = {
            "Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu", 
            "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu"
        }
        hari_en = w_skrg.strftime("%A")
        hari_id = hari_map.get(hari_en, hari_en) # Default jika tidak ditemukan

        tgl_str = w_skrg.strftime(f"{hari_id}, %d %B %Y").replace("January", "Januari").replace("February", "Februari").replace("March", "Maret").replace("April", "April").replace("May", "Mei").replace("June", "Juni").replace("July", "Juli").replace("August", "Agustus").replace("September", "September").replace("October", "Oktober").replace("November", "November").replace("December", "Desember")

        jam_str = w_skrg.strftime("%H:%M:%S") + " WIB"
        text_watermark = f"{nama}\n{jam_str}\n{tgl_str}"
        
        # Ukuran font dinamis (sekitar 3% dari lebar gambar)
        font_size = int(img.width * 0.035)
        try:
            # Memuat font default PIL yang cenderung lebih umum tersedia
            font = ImageFont.load_default(size=font_size) 
        except Exception as e:
            st.warning(f"Gagal memuat font: {e}. Menggunakan font default.")
            font = ImageFont.load_default() # Fallback

        # Posisi teks (Pojok kiri bawah dengan margin)
        margin = 20
        # Jarak antar baris di multiline_text
        line_spacing = 6
        
        # Hitung tinggi total teks agar posisi tepat
        # dummy_draw untuk mengukur teks (butuh font untuk ini)
        if hasattr(font, 'getbbox'): # PIL 9+
            bbox = font.getbbox("Tg") # contoh karakter untuk estimasi tinggi baris
            line_height = bbox[3] - bbox[1]
        else: # PIL lama
            line_height = font_size + 2 # estimasi kasar

        text_height_total = len(text_watermark.split('\n')) * line_height + (len(text_watermark.split('\n')) - 1) * line_spacing

        # Posisi Y untuk teks watermark (dari bawah ke atas)
        y_position = img.height - text_height_total - margin

        # Menambahkan bayangan (shadow) hitam agar teks terbaca di background terang/gelap
        draw.multiline_text(
            (margin + 2, y_position + 2), 
            text_watermark, 
            fill=(0, 0, 0), # Shadow color
            font=font, 
            spacing=line_spacing
        )
        draw.multiline_text(
            (margin, y_position), 
            text_watermark, 
            fill=(255, 255, 255), # Main text color
            font=font, 
            spacing=line_spacing
        )
        
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
        st.error(f"Terjadi error saat mengirim data: {e}")
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
            with st.status("Sedang memproses & mengirim data absensi...", expanded=True) as s:
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
    
    # Konversi Hari & Bulan ke Bahasa Indonesia untuk tampilan sidebar
    hari_map = {
        "Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu", 
        "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu"
    }
    bulan_map = {
        "January": "Januari", "February": "Februari", "March": "Maret", "April": "April",
        "May": "Mei", "June": "Juni", "July": "Juli", "August": "Agustus",
        "September": "September", "October": "Oktober", "November": "November", "December": "Desember"
    }
    
    hari_en = w.strftime("%A")
    hari_id = hari_map.get(hari_en, hari_en)
    
    bulan_en = w.strftime("%B")
    bulan_id = bulan_map.get(bulan_en, bulan_en)

    tgl_full = w.strftime(f"{hari_id}, %d {bulan_id} %Y")

    st.markdown(f'''<div class="sidebar-box"><span style="color:white">{tgl_full}</span><br>
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
                konfirmasi_dialog(nama, status_sesi, foto, w_skrg)
            else:
                st.warning("📸 Silakan ambil foto terlebih dahulu!")

# --- HALAMAN 📊 REKAP ABSENSI ---
else:
    st.markdown("<h2 style='text-align:center; color:white;'>📊 Rekap Absensi Bulanan</h2>", unsafe_allow_html=True)
    list_b = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    
    c1, c2 = st.columns(2)
    b = c1.selectbox("Pilih Bulan:", list_b, index=w_skrg.month - 1)
    t = c2.selectbox("Pilih Tahun:", [2025, 2026, 2027], index=1) # Diperluas hingga 2027

    if st.button("🔍 Tampilkan Data Rekap", use_container_width=True):
        try:
            res = requests.get(f"{WEBAPP_URL}?bulan={b} {t}", timeout=25).json()
            if res:
                df = pd.DataFrame(res)
                df.insert(0, 'No', range(1, 1 + len(df)))
                
                # Mengubah nama kolom jika 'Lokasi' ada dan ingin disembunyikan di rekap
                if 'Lokasi' in df.columns:
                    df = df.rename(columns={'Lokasi': 'Detail Lokasi (Foto)'}) # Ubah nama kolom agar lebih jelas
                if 'Link Foto' in df.columns:
                    df = df.drop(columns=['Link Foto']) # Sembunyikan link foto mentah dari tabel utama
                
                st.dataframe(
                    df, # Tampilkan semua kolom yang tersisa setelah di drop/rename
                    hide_index=True, 
                    use_container_width=True,
                    column_config={
                        "No": st.column_config.Column("No", width="small"),
                        "Nama": st.column_config.Column("Nama", width="medium"),
                        # Tambahan untuk melihat foto watermark
                        "Detail Lokasi (Foto)": st.column_config.ImageColumn(
                            "Detail Lokasi (Foto)", help="Tautan foto dengan watermark", width="large"
                        )
                    }
                )
                
            else:
                st.info(f"Data absensi untuk periode {b} {t} belum tersedia.")
        except Exception as e:
            st.error(f"Gagal mengambil data dari Spreadsheet: {e}")
