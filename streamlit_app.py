import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import time

# --- KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
# PASTI GANTI DENGAN URL APPS SCRIPT BARU SETIAP KALI DEPLOY
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwfHQNijEvLjrbsTy5o6Yl0IQX9ynvCC4wBiZypODS9cxQFp-zbheqDvvzyF3gzqGI/exec"

st.set_page_config(page_title="Absensi Tim KI PPS Banten", layout="wide")

# CSS: Custom Look & Camera Mirror Fix
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

def olah_foto(foto, nama, status, w_skrg):
    try:
        img = Image.open(foto).convert("RGB")
        img = ImageOps.mirror(img) # Menghilangkan efek mirror
        draw = ImageDraw.Draw(img)
        hari_list = {"Monday":"Senin","Tuesday":"Selasa","Wednesday":"Rabu","Thursday":"Kamis","Friday":"Jumat","Saturday":"Sabtu","Sunday":"Minggu"}
        hari_id = hari_list.get(w_skrg.strftime("%A"), w_skrg.strftime("%A"))
        
        teks_wm = f"NAMA: {nama}\nSTATUS: {status}\nJAM: {w_skrg.strftime('%H:%M:%S')} WIB\nTANGGAL: {hari_id}, {w_skrg.strftime('%d %B %Y')}"
        font = ImageFont.load_default()
        
        # Pojok Kiri Bawah
        x, y = 25, img.height - 110
        draw.multiline_text((x+2, y+2), teks_wm, fill="black", font=font, spacing=4) # Shadow
        draw.multiline_text((x, y), teks_wm, fill="white", font=font, spacing=4) # Main text
        
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return buf.getvalue()
    except Exception as e:
        st.error(f"Error proses foto: {e}")
        return None

@st.dialog("Konfirmasi Absensi")
def dialog_konfirmasi(nama, status, foto_raw, w_skrg):
    st.warning(f"Kirim data absen **{status}** untuk **{nama}**?")
    if st.button("YA, KIRIM SEKARANG", use_container_width=True, type="primary"):
        with st.status("Sedang memproses...") as s:
            foto_final = olah_foto(foto_raw, nama, status, w_skrg)
            if foto_final:
                # Upload ke ImgBB
                res_img = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": foto_final}).json()
                link_url = res_img["data"]["url"]
                # Kirim ke Sheets
                payload = {"nama": nama, "tanggal": w_skrg.strftime("%Y-%m-%d"), "jam": w_skrg.strftime("%H:%M:%S"), "status": status, "foto_link": link_url}
                requests.post(WEBAPP_URL, json=payload, timeout=20)
                s.update(label="✅ Berhasil Terkirim!", state="complete")
                st.balloons()
                time.sleep(2)
                st.rerun()

@st.fragment(run_every="1s")
def jam_sidebar():
    w = datetime.datetime.now() + datetime.timedelta(hours=7)
    st.markdown(f'''<div class="sidebar-box">{w.strftime("%d %B %Y")}<br>
    <span style="font-size:26px; font-weight:bold; color:#3b82f6;">{w.strftime("%H:%M:%S")}</span><br>WIB</div>''', unsafe_allow_html=True)
    return w

# --- LOGIKA UI ---
with st.sidebar:
    st.header("🏢 MENU UTAMA")
    menu = st.selectbox("Layanan:", ["📍 Absensi", "📊 Rekap Data"])
    st.divider()
    w_skrg = jam_sidebar()

if menu == "📍 Absensi":
    st.title("📍 Absensi Kehadiran")
    # Jam 06-12 Masuk, Jam 12-23 Pulang
    status_aktif = "MASUK" if 6 <= w_skrg.hour < 12 else "PULANG" if 12 <= w_skrg.hour < 23 else "TUTUP"
    
    if status_aktif == "TUTUP":
        st.error("🚫 Sesi Absensi Ditutup.")
    else:
        st.info(f"Sesi: **{status_aktif}**")
        nama_list = ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"]
        nama_user = st.selectbox("Pilih Nama:", nama_list)
        foto_input = st.camera_input("Ambil Foto Wajah")
        
        if st.button("KIRIM ABSENSI", use_container_width=True, type="primary"):
            if foto_input: dialog_konfirmasi(nama_user, status_aktif, foto_input, w_skrg)
            else: st.warning("📸 Foto belum diambil!")

else:
    st.title("📊 Rekap Data Absensi")
    list_bln = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    c1, c2 = st.columns(2)
    with c1: b = st.selectbox("Bulan:", list_bln, index=w_skrg.month - 1)
    with c2: t = st.selectbox("Tahun:", [2025, 2026], index=1)
    
    if st.button("🔍 Tampilkan Rekap", use_container_width=True):
        try:
            res = requests.get(f"{WEBAPP_URL}?bulan={b} {t}", timeout=25).json()
            if res:
                df = pd.DataFrame(res)
                df.insert(0, 'No', range(1, 1 + len(df)))
                st.dataframe(df, hide_index=True, use_container_width=True)
            else:
                st.info("Data belum tersedia untuk periode ini.")
        except:
            st.error("Gagal mengambil data. Pastikan Apps Script sudah di-Deploy ulang.")
