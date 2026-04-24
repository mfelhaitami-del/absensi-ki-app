import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import time

# --- KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
# GANTI DENGAN URL DEPLOYMENT BARU ANDA
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwAioVaa0D2lrO02sXOHwoPW3A_PjxixG57rMbSClkIiFIsC7oWAEoONdtkJ15rbtk/exec"

st.set_page_config(page_title="Absensi Tim KI Satker PPS", layout="wide")

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

NAMA_PEGAWAI = [
    "Mulyaman Ramimpus (Driver 1)", "Umar Hadapi (Driver 2)", "Asep Pudin (Security 1)", 
    "M. Abdu Rahman (Security 2)", "Mustaji (Pramubakti 1)", "Ii Safii (Pramubakti 2)"
]

def olah_foto(foto, nama, status, w_skrg):
    try:
        img = Image.open(foto).convert("RGB")
        img = ImageOps.mirror(img)
        draw = ImageDraw.Draw(img)
        hari_dict = {"Monday":"Senin","Tuesday":"Selasa","Wednesday":"Rabu","Thursday":"Kamis","Friday":"Jumat","Saturday":"Sabtu","Sunday":"Minggu"}
        hari_id = hari_dict.get(w_skrg.strftime("%A"), w_skrg.strftime("%A"))
        
        # Watermark tetap menggunakan jam lokal HP untuk info di foto
        teks_wm = f"NAMA: {nama}\nSTATUS: {status}\nJAM: {w_skrg.strftime('%H:%M:%S')} WIB\nTANGGAL: {hari_id}, {w_skrg.strftime('%d %B %Y')}"
        font = ImageFont.load_default()
        
        draw.multiline_text((22, img.height-112), teks_wm, fill="black", font=font, spacing=4)
        draw.multiline_text((20, img.height-110), teks_wm, fill="white", font=font, spacing=4)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return buf.getvalue()
    except: return None

@st.dialog("Konfirmasi")
def konfirmasi_absen(nama, status, foto_raw, w_skrg):
    st.write(f"Kirim absen **{status}** untuk **{nama}**?")
    if st.button("YA, KIRIM", use_container_width=True, type="primary"):
        with st.status("Sedang mengirim...") as s:
            foto_final = olah_foto(foto_raw, nama, status, w_skrg)
            if foto_final:
                res_img = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files={"image": foto_final}).json()
                link_url = res_img["data"]["url"]
                
                # Payload: Jam tidak dikirim dari sini agar tidak ada selisih
                payload = {"nama": nama, "status": status, "foto_link": link_url, "tanggal": w_skrg.strftime("%Y-%m-%d")}
                requests.post(WEBAPP_URL, json=payload, timeout=20)
                
                s.update(label="✅ Berhasil!", state="complete")
                time.sleep(1)
                st.rerun()

@st.fragment(run_every="1s")
def jam_sidebar():
    w = datetime.datetime.now() + datetime.timedelta(hours=7)
    st.markdown(f'''<div class="sidebar-box">{w.strftime("%d %B %Y")}<br><span style="font-size:26px; font-weight:bold; color:#3b82f6;">{w.strftime("%H:%M:%S")}</span><br>WIB</div>''', unsafe_allow_html=True)
    return w

with st.sidebar:
    st.header("🏢 MENU")
    menu = st.selectbox("Layanan:", ["📍 Absensi", "📊 Rekap Data"])
    st.divider()
    w_skrg = jam_sidebar()

if menu == "📍 Absensi":
    st.title("📍 Absensi")
    status_sesi = "MASUK" if 6 <= w_skrg.hour < 12 else "PULANG" if 12 <= w_skrg.hour < 23 else "TUTUP"
    if status_sesi == "TUTUP": st.error("🚫 Sesi Absensi Tutup")
    else:
        nama_pilih = st.selectbox("Pilih Nama:", NAMA_PEGAWAI)
        foto_cap = st.camera_input("Ambil Foto")
        if st.button("KIRIM DATA", use_container_width=True, type="primary"):
            if foto_cap: konfirmasi_absen(nama_pilih, status_sesi, foto_cap, w_skrg)
            else: st.warning("📸 Foto belum diambil!")
else:
    st.title("📊 Rekap Data Absensi")
    list_bln = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    c1, c2 = st.columns(2)
    b = c1.selectbox("Bulan:", list_bln, index=w_skrg.month-1); t = c2.selectbox("Tahun:", [2025, 2026], index=1)
    
    if st.button("🔍 Tampilkan Rekap", use_container_width=True):
        try:
            res = requests.get(f"{WEBAPP_URL}?bulan={b} {t}", timeout=25).json()
            if res:
                df = pd.DataFrame(res)
                # Paksa kolom jam menjadi teks agar Streamlit tidak mengubah zona waktu
                df['Jam Masuk'] = df['Jam Masuk'].astype(str)
                df['Jam Pulang'] = df['Jam Pulang'].astype(str)
                df.insert(0, 'No', range(1, 1 + len(df)))
                st.dataframe(df, hide_index=True, use_container_width=True)
            else: st.info("Data belum tersedia.")
        except: st.error("Gagal terhubung ke server.")
