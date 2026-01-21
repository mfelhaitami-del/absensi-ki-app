import streamlit as st
from st-gsheets-connection import GSheetsConnection
import pandas as pd
import datetime
import requests
from io import BytesIO

# --- KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# Koneksi ke Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Logika Waktu WIB
waktu_wib = datetime.datetime.now() + datetime.timedelta(hours=7)
tgl_sekarang = waktu_wib.strftime("%Y-%m-%d")

# Sidebar
st.sidebar.title("Navigasi")
menu = st.sidebar.radio("Menu", ["📍 Presensi", "🗄️ Arsip Website"])

if menu == "📍 Presensi":
    st.header("📍 Presensi Kehadiran")
    daftar_nama = ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"]
    
    nama = st.selectbox("Pilih Nama", daftar_nama)
    foto = st.camera_input("Ambil Foto")

    if st.button("Kirim Absen"):
        if foto:
            with st.spinner("Menyimpan data..."):
                # 1. Upload ke ImgBB
                files = {"image": foto.getvalue()}
                resp = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files=files)
                link_foto = resp.json()["data"]["url"]

                # 2. Ambil Data Lama & Tambah Baru
                df_lama = conn.read(ttl=0).dropna(how="all")
                data_baru = pd.DataFrame([{
                    "Nama": nama, "Tanggal": tgl_sekarang, 
                    "Jam": waktu_wib.strftime("%H:%M:%S"), 
                    "Foto_Link": link_foto,
                    "Preview_Foto": f'=IMAGE("{link_foto}")'
                }])
                df_final = pd.concat([df_lama, data_baru], ignore_index=True)

                # 3. Update ke Sheets
                conn.update(data=df_final)
                st.cache_data.clear()
                st.success(f"✅ Berhasil absen jam {waktu_wib.strftime('%H:%M:%S')}")
        else:
            st.error("Foto wajib diambil!")

elif menu == "🗄️ Arsip Website":
    st.header("🗄️ Arsip Absensi")
    try:
        df_view = conn.read(ttl=0).dropna(how="all")
        st.dataframe(df_view, use_container_width=True)

        # Tombol Download Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_view.to_excel(writer, index=False)
        st.download_button("📥 Download Excel", output.getvalue(), f"Absensi_{tgl_sekarang}.xlsx")
    except:

        st.info("Belum ada data.")


