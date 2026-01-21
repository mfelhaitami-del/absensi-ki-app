import streamlit as st
import pandas as pd
import datetime
import requests
import json

# --- KONFIGURASI ---
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"
# Masukkan URL Google Sheets Anda (Pastikan sudah di-share sebagai EDITOR ke email service account)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1mWpkwIy4bmsEEit21BE4qnKflS5Pbcn643lhTm7_S-4/edit?gid=0#gid=0"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# Logika Waktu WIB
waktu_wib = datetime.datetime.now() + datetime.timedelta(hours=7)
tgl_sekarang = waktu_wib.hour

st.sidebar.title("Navigasi")
menu = st.sidebar.radio("Menu", ["📍 Presensi", "🗄️ Arsip Sesi Ini"])

if 'data_lokal' not in st.session_state:
    st.session_state.data_lokal = []

if menu == "📍 Presensi":
    st.header("📍 Presensi Kehadiran")
    daftar_nama = ["Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"]
    
    nama = st.selectbox("Pilih Nama", daftar_nama)
    foto = st.camera_input("Ambil Foto")

    if st.button("Kirim Absen"):
        if foto:
            with st.spinner("Mengupload foto..."):
                # 1. Upload ke ImgBB
                files = {"image": foto.getvalue()}
                resp = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files=files)
                link_foto = resp.json()["data"]["url"]
                
                jam_skrg = waktu_wib.strftime("%H:%M:%S")
                
                # 2. Simpan ke Sesi Website (Arsip Langsung Muncul)
                st.session_state.data_lokal.append({
                    "Nama": nama,
                    "Tanggal": waktu_wib.strftime("%Y-%m-%d"),
                    "Jam": jam_skrg,
                    "Link Foto": link_foto
                })
                
                st.success(f"✅ Berhasil! Foto tersimpan. Jangan lupa download laporan di menu Arsip.")
        else:
            st.error("Ambil foto dulu!")

elif menu == "🗄️ Arsip Sesi Ini":
    st.header("🗄️ Arsip Data")
    if st.session_state.data_lokal:
        df = pd.DataFrame(st.session_state.data_lokal)
        st.dataframe(df, use_container_width=True)
        
        # Tombol Download CSV (Lebih aman dari Excel agar tidak butuh library tambahan)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Data (CSV)", csv, "absensi.csv", "text/csv")
    else:
        st.info("Belum ada data untuk sesi ini.")
