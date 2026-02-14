import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import time

# --- KONFIGURASI (PASTIKAN DIISI BENAR) ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
# Ganti dengan URL /exec terbaru dari New Deployment Google Apps Script Anda
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbyW4nxjMP4XzDIgGelbawm6GlotqHg4Rh7L1CxURNgaPJ9rz1oMYoALjfuqNdU3UE0I/exec"

st.set_page_config(page_title="Absensi Tim KI Satker PPS", layout="wide")

# --- CSS: CUSTOM UI ---
st.markdown("""
    <style>
    [data-testid="stCameraInput"] video { transform: scaleX(-1); border-radius: 15px; border: 2px solid #3b82f6; }
    .stApp {
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
        url("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Logo_PU_%28RGB%29.jpg/960px-Logo_PU_%28RGB%29.jpg");
        background-size: cover; background-attachment: fixed;
    }
    .sidebar-box { background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #3b82f6; color: white; }
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI OLAH GAMBAR (ANTI-MIRROR & WATERMARK) ---
def proses_foto_absensi(foto_input, nama, status, w_skrg):
    try:
        img = Image.open(foto_input).convert("RGB")
        img = ImageOps.mirror(img)  # Membalikkan foto agar hasil normal (tidak mirror)
        draw = ImageDraw.Draw(img)
        
        # Penamaan Hari Indonesia
        hari_list = {"Monday":"Senin","Tuesday":"Selasa","Wednesday":"Rabu","Thursday":"Kamis","Friday":"Jumat","Saturday":"Sabtu","Sunday":"Minggu"}
        hari_id = hari_list.get(w_skrg.strftime("%A"), w_skrg.strftime("%A"))
        
        teks_watermark = (
            f"NAMA: {nama}\n"
            f"STATUS: {status}\n"
            f"JAM: {w_skrg.strftime('%H:%M:%S')} WIB\n"
            f"TANGGAL: {hari_id}, {w_skrg.strftime('%d %B %Y')}"
        )
        
        # Gunakan font default (kompatibel dengan Streamlit Cloud)
        font = ImageFont.load_default()
        
        # Posisi Kiri Bawah
        x, y = 20, img.height - 120
        
        # Gambar Bayangan (Shadow) Hitam agar teks putih terbaca
        draw.multiline_text((x+2, y+2), teks_watermark, fill="black", font=font, spacing=5)
        # Gambar Teks Utama Putih
        draw.multiline_text((x, y), teks_watermark, fill="white", font=font, spacing=5)
        
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return buf.getvalue()
    except Exception as e:
        st.error(f"Gagal memproses gambar: {e}")
        return None

# --- DIALOG KONFIRMASI ---
@st.dialog("Konfirmasi Pengiriman")
def konfirmasi_kirim(nama, status, foto_raw, w_skrg):
    st.warning(f"Apakah Anda yakin ingin mengirim absen **{status}**?")
    st.write(f"Nama: **{nama}**")
    
    if st.button("YA, KIRIM DATA", use_container_width=True, type="primary"):
        with st.status("Memproses...", expanded=True) as s:
            # 1. Olah Watermark
            foto_final = proses_foto_absensi(foto_raw, nama, status, w_skrg)
            if not foto_final: return
            
            # 2. Upload ke ImgBB
            try:
                s.write("📤 Mengunggah foto...")
                res_img = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": foto_final}).json()
                link_url = res_img["data"]["url"]
                
                # 3. Kirim ke Google Sheets
                s.write("📝 Mencatat di spreadsheet...")
                payload = {
                    "nama": nama, 
                    "tanggal": w_skrg.strftime("%Y-%m-%d"), 
                    "jam": w_skrg.strftime("%H:%M:%S"), 
                    "status": status, 
                    "foto_link": link_url
                }
                requests.post(WEBAPP_URL, json=payload, timeout=20)
                
                s.update(label="✅ Berhasil!", state="complete")
                st.balloons()
                time.sleep(2)
                st.rerun()
            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")

# --- JAM REAL-TIME SIDEBAR ---
@st.fragment(run_every="1s")
def jam_digital():
    # Menyesuaikan waktu ke WIB (UTC+7)
    w = datetime.datetime.now() + datetime.timedelta(hours=7)
    st.markdown(f'''<div class="sidebar-box">
        {w.strftime("%d %B %Y")}<br>
        <span style="font-size:26px; font-weight:bold; color:#3b82f6;">{w.strftime("%H:%M:%S")}</span><br>
        WIB</div>''', unsafe_allow_html=True)
    return w

# --- STRUKTUR UI ---
with st.sidebar:
    st.title("🏢 MENU")
    menu = st.selectbox("Pilih Layanan:", ["📍 Absensi", "📊 Rekap Data"])
    st.divider()
    w_skrg = jam_digital()

if menu == "📍 Absensi":
    st.title("📍 Absensi Kehadiran")
    
    # Deteksi Sesi Otomatis
    status_sesi = "MASUK" if 6 <= w_skrg.hour < 12 else "PULANG" if 12 <= w_skrg.hour < 23 else "TUTUP"
    
    if status_sesi == "TUTUP":
        st.error("🚫 Sesi Absensi Ditutup (06:00 - 23:00 WIB)")
    else:
        st.info(f"Sesi Aktif: **{status_sesi}**")
        nama_list = ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"]
        nama_pilih = st.selectbox("Pilih Nama Anda:", nama_list)
        
        foto_cap = st.camera_input("Ambil Foto Wajah")
        
        if st.button("KIRIM ABSENSI", use_container_width=True, type="primary"):
            if foto_cap:
                konfirmasi_kirim(nama_pilih, status_sesi, foto_cap, w_skrg)
            else:
                st.warning("📸 Silakan ambil foto dulu!")

else:
    st.title("📊 Rekap Absensi")
    list_bulan = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    
    c1, c2 = st.columns(2)
    b = c1.selectbox("Bulan:", list_bulan, index=w_skrg.month - 1)
    t = c2.selectbox("Tahun:", [2025, 2026], index=1)
    
    if st.button("🔍 Tampilkan Rekap", use_container_width=True):
        try:
            # Mengambil data rekap melalui fungsi doGet di Apps Script
            response = requests.get(f"{WEBAPP_URL}?bulan={b} {t}", timeout=25)
            data_rekap = response.json()
            
            if data_rekap:
                df = pd.DataFrame(data_rekap)
                df.insert(0, 'No', range(1, 1 + len(df)))
                st.dataframe(df, hide_index=True, use_container_width=True)
            else:
                st.info(f"Tidak ada data untuk periode {b} {t}")
        except:
            st.error("Gagal terhubung ke server. Pastikan URL Apps Script sudah benar.")
