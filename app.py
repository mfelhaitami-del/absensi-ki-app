import streamlit as st
import pandas as pd
import datetime
import requests
from PIL import Image, ImageOps
from io import BytesIO

# --- KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzYQNPs6BWoNNLJt1vVi4ro8Nj2D4KiGKwhss2_wYBbVx3tcnoOiKC3Z0AXiG7wwstp/exec"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# Logika Waktu
waktu_wib = datetime.datetime.now() + datetime.timedelta(hours=7)
tgl_hari_ini = waktu_wib.strftime("%Y-%m-%d")

# --- SIDEBAR NAVIGASI ---
menu = st.sidebar.selectbox("Pilih Menu", ["📍 Presensi", "📊 Rekap Absensi"])

if menu == "📍 Presensi":
    st.title("📸 Absensi Foto Real-Time")
    daftar_nama = ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"]
    
    nama = st.selectbox("Pilih Nama Anda", daftar_nama)
    foto = st.camera_input("Ambil Foto Wajah")

    if st.button("Kirim Absen"):
        if foto:
            with st.spinner("Mengirim data..."):
                try:
                    # Proses Non-Mirror
                    img = Image.open(foto)
                    img_real = ImageOps.mirror(img)
                    buf = BytesIO()
                    img_real.save(buf, format="JPEG")
                    byte_im = buf.getvalue()

                    # Upload ImgBB
                    files = {"image": byte_im}
                    resp = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files=files)
                    link_foto = resp.json()["data"]["url"]

                    # Kirim ke Sheets
                    data = {
                        "nama": nama,
                        "tanggal": tgl_hari_ini,
                        "jam": waktu_wib.strftime("%H:%M:%S"),
                        "foto_link": link_foto
                    }
                    requests.post(WEBAPP_URL, json=data)
                    st.success(f"✅ Berhasil! Absensi {nama} tercatat.")
                except Exception as e:
                    st.error(f"Gagal: {e}")
        else:
            st.warning("Ambil foto dulu!")

elif menu == "📊 Rekap Absensi":
    st.title("📊 Rekap Absensi Tim KI")
    st.write(f"Data absensi yang tercatat di Google Sheets (Per {tgl_hari_ini})")
    
    if st.button("🔄 Segarkan Data"):
        st.cache_data.clear()

    with st.spinner("Mengambil data dari Google Sheets..."):
        try:
            # Ambil data lewat Apps Script (GET request)
            response = requests.get(WEBAPP_URL)
            all_data = response.json()
            
            if all_data:
                df = pd.DataFrame(all_data)
                
                # Mengatur tampilan tabel
                df = df[["nama", "tanggal", "jam", "foto_link"]]
                
                # Menampilkan tabel interaktif
                st.dataframe(df, use_container_width=True)
                
                # Tombol Download Excel/CSV
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Data (CSV)", csv, f"rekap_absensi_{tgl_hari_ini}.csv", "text/csv")
            else:
                st.info("Belum ada data absensi di Google Sheets.")
        except Exception as e:
            st.error(f"Gagal mengambil data: {e}")
