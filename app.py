import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import time

# --- KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxuH6AdWUeMkWagwsnYqhWO8_d_sgN0TO2TSBilPb7uiCFvx3MqoquFpx6TdAVmeLGV/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# --- CSS: BACKGROUND & KAMERA ---
st.markdown("""
    <style>
    /* Viewfinder tetap mirror agar user nyaman mengatur posisi wajah */
    [data-testid="stCameraInput"] video { transform: scaleX(-1); border-radius: 15px; border: 2px solid #3b82f6; }
    
    .stApp {
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
        url("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Logo_PU_%28RGB%29.jpg/960px-Logo_PU_%28RGB%29.jpg");
        background-size: cover; background-attachment: fixed;
    }
    .sidebar-box { 
        background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #3b82f6; 
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI WATERMARK (POJOK KIRI BAWAH) ---
def proses_watermark(img_input, nama, status, w_skrg):
    try:
        # Gunakan salinan gambar agar tidak merusak preview
        img = img_input.copy()
        draw = ImageDraw.Draw(img)
        
        hari_id = w_skrg.strftime("%A").replace("Monday","Senin").replace("Tuesday","Selasa").replace("Wednesday","Rabu").replace("Thursday","Kamis").replace("Friday","Jumat").replace("Saturday","Sabtu").replace("Sunday","Minggu")
        tgl_str = w_skrg.strftime(f"{hari_id}, %d %B %Y")
        jam_str = w_skrg.strftime("%H:%M:%S") + " WIB"
        
        # Teks Watermark
        watermark_text = f"NAMA: {nama}\nSTATUS: {status}\nJAM: {jam_str}\nTANGGAL: {tgl_str}"
        
        # Ukuran font dinamis
        f_size = int(img.width * 0.035)
        try:
            font = ImageFont.load_default(size=f_size)
        except:
            font = ImageFont.load_default()

        # Posisi Pojok Kiri Bawah
        margin_x = 25
        line_height = f_size + 5
        margin_y = img.height - (line_height * 4) - 30 
        
        # Gambar Bayangan (Hitam) & Teks (Putih)
        draw.multiline_text((margin_x + 2, margin_y + 2), watermark_text, fill=(0,0,0), font=font, spacing=5)
        draw.multiline_text((margin_x, margin_y), watermark_text, fill=(255,255,255), font=font, spacing=5)
        
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        return buf.getvalue()
    except Exception as e:
        st.error(f"Error Watermark: {e}")
        return None

# --- FUNGSI KIRIM DATA ---
def kirim_data(nama, status, foto_bytes, w_skrg):
    try:
        # 1. Upload ke ImgBB
        res_img = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": foto_bytes}).json()
        link_foto = res_img["data"]["url"]
        
        # 2. Payload Sheets
        payload = {
            "nama": nama, "tanggal": w_skrg.strftime("%Y-%m-%d"), 
            "jam": w_skrg.strftime("%H:%M:%S"), "status": status, "foto_link": link_foto
        }
        response = requests.post(WEBAPP_URL, json=payload, timeout=20)
        return response.status_code == 200
    except:
        return False

# --- DIALOG KONFIRMASI (ANTI-MIRROR PREVIEW) ---
@st.dialog("Konfirmasi Absensi")
def konfirmasi_dialog(nama, status, img_normal, w_skrg):
    st.warning("⚠️ Periksa kembali foto dan nama Anda!")
    
    # TAMPILKAN PREVIEW YANG SUDAH TIDAK MIRROR
    st.image(img_normal, caption="Hasil Jepretan (Posisi Normal)", use_container_width=True)
    
    st.write(f"Nama: **{nama}**")
    st.write(f"Status: **{status}**")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Ya, Kirim Sekarang", use_container_width=True, type="primary"):
            with st.status("Memproses & Mengirim...", expanded=False) as s:
                # Proses watermark menggunakan gambar yang sudah normal
                foto_final = proses_watermark(img_normal, nama, status, w_skrg)
                if foto_final and kirim_data(nama, status, foto_final, w_skrg):
                    s.update(label="✅ Absensi Berhasil!", state="complete")
                    st.toast("Data telah tersimpan di Google Sheets", icon="✅")
                    time.sleep(2)
                    st.rerun()
                else:
                    s.update(label="❌ Gagal mengirim data!", state="error")
    with col2:
        if st.button("Batal / Ambil Ulang", use_container_width=True):
            st.rerun()

# --- JAM SIDEBAR (FRAGMENT) ---
@st.fragment(run_every="1s")
def jam_sidebar():
    w = datetime.datetime.now() + datetime.timedelta(hours=7)
    st.markdown(f'''<div class="sidebar-box">
        <span style="color:white; font-size:14px;">{w.strftime("%d %B %Y")}</span><br>
        <span style="font-size:26px; color:#3b82f6; font-weight:bold;">{w.strftime("%H:%M:%S")}</span><br>
        <small style="color:white;">WIB</small>
    </div>''', unsafe_allow_html=True)
    return w

# --- UI UTAMA ---
with st.sidebar:
    st.header("🏢 MENU UTAMA")
    menu = st.selectbox("Pilih Layanan:", ["📍 Absensi", "📊 Rekap"])
    st.divider()
    w_skrg = jam_sidebar()

if menu == "📍 Absensi":
    st.markdown("<h2 style='text-align:center; color:white;'>Absensi Tim KI Satker PPS Banten</h2>", unsafe_allow_html=True)
    
    status_sesi = "MASUK" if 6 <= w_skrg.hour < 12 else "PULANG" if 12 <= w_skrg.hour < 23 else "TUTUP"
    
    if status_sesi == "TUTUP":
        st.error("🚫 Sesi Absensi ditutup (Buka jam 06:00 - 23:00 WIB)")
    else:
        st.info(f"Sesi Aktif: **{status_sesi}**")
        nama_user = st.selectbox("Pilih Nama Anda:", ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"])
        
        foto_input = st.camera_input("Ambil Foto Wajah")
        
        if foto_input:
            # --- LOGIKA ANTI-MIRROR SEBELUM PREVIEW ---
            # Kita buka foto dan balikkan secara horizontal (mirror)
            img_raw = Image.open(foto_input).convert("RGB")
            img_normal = ImageOps.mirror(img_raw) 
            
            # Tampilkan tombol konfirmasi
            if st.button("KIRIM DATA ABSENSI", use_container_width=True, type="primary"):
                konfirmasi_dialog(nama_user, status_sesi, img_normal, w_skrg)
        else:
            st.warning("📸 Silakan ambil foto wajah untuk mengaktifkan tombol kirim.")
else:
    st.markdown("<h2 style='text-align:center; color:white;'>📊 Rekap Absensi</h2>", unsafe_allow_html=True)
    st.write("Data dapat Anda akses langsung melalui link Google Sheets atau dashboard backend.")
