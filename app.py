import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image, ImageOps
from io import BytesIO

# --- KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzDDGyZ3Dd6WULlAe33zOd6xdihasTMVDVN_6xxaDFMV-54hmAqvE4B1Wm58OpOqhpD/exec"

st.set_page_config(page_title="Absensi KI", layout="wide")

waktu_now = datetime.datetime.now() + datetime.timedelta(hours=7)
tgl_skrg = waktu_now.strftime("%Y-%m-%d")
jam_skrg_int = waktu_now.hour

# Penentuan Status
status_absen = None
if 6 <= jam_skrg_int < 12:
    status_absen = "MASUK"
elif 13 <= jam_skrg_int < 22:
    status_absen = "PULANG"
else:
    status_absen = "TUTUP"

menu = st.sidebar.selectbox("Pilih Menu", ["📍 Absensi", "📊 Rekap Absensi"])

if menu == "📍 Absensi":
    st.title("📸 Absensi Tim KI Satker PPS Banten")
    st.info(f"📅 {tgl_skrg} | ⏰ {waktu_now.strftime('%H:%M:%S')}")
    
    if status_absen == "TUTUP":
        st.error("Sistem Absensi Sedang Tutup (Buka: 06-12 & 13-18)")
    else:
        st.subheader(f"Sesi: ABSEN {status_absen}")
        daftar_nama = ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"]
        nama = st.selectbox("Pilih Nama", daftar_nama)
        foto = st.camera_input("Ambil Foto")

        if st.button(f"Kirim Absen {status_absen}"):
            if foto:
                with st.spinner("Mengupload data..."):
                    try:
                        img = Image.open(foto)
                        img_real = ImageOps.mirror(img) # Mengatasi mirror
                        buf = BytesIO()
                        img_real.save(buf, format="JPEG")
                        
                        files = {"image": buf.getvalue()}
                        resp = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files=files)
                        link_foto = resp.json()["data"]["url"]

                        payload = {
                            "nama": nama, "tanggal": tgl_skrg, 
                            "jam": waktu_now.strftime("%H:%M:%S"),
                            "status": status_absen, "foto_link": link_foto
                        }
                        requests.post(WEBAPP_URL, json=payload)
                        st.success(f"✅ Berhasil! Foto sudah masuk ke Spreadsheet.")
                    except:
                        st.error("Terjadi kesalahan saat upload.")
            else:
                st.warning("Ambil foto dulu!")

elif menu == "📊 Rekap Absensi":
    st.title("📊 Rekap Absensi")
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
    
    try:
        res = requests.get(WEBAPP_URL)
        df = pd.DataFrame(res.json())
        if not df.empty:
            df.columns = ["Nama", "Tanggal", "Jam Masuk", "Jam Pulang", "Link Foto"]
            # Tampilkan tabel dengan kolom link yang bisa diklik
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Belum ada data.")
    except:
        st.error("Gagal mengambil data rekap.")


