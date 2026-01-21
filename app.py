import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import requests
from io import BytesIO

# --- 1. KONFIGURASI API ---
# Pastikan API Key ImgBB Anda benar
API_IMGBB = "4c3fb57e24494624fd12e23156c0c6b0"

st.set_page_config(page_title="Absensi Tim KI", layout="wide")

# --- 2. KONEKSI GOOGLE SHEETS ---
# Kode ini akan otomatis membaca [connections.gsheets] dari Secrets Anda
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. LOGIKA WAKTU WIB ---
waktu_wib = datetime.datetime.now() + datetime.timedelta(hours=7)
tgl_sekarang = waktu_wib.strftime("%Y-%m-%d")
jam_skrg = waktu_wib.strftime("%H:%M:%S")

st.sidebar.title("Navigasi")
menu = st.sidebar.radio("Menu", ["📍 Presensi", "🗄️ Arsip Website"])

if menu == "📍 Presensi":
    st.header("📍 Presensi Kehadiran")
    
    daftar_nama = [
        "Diana Lestari", "Tuhfah Aqdah Agna", "Dini Atsqiani", 
        "Leily Chusnul Makrifah", "Mochamad Fajar Elhaitami", 
        "Muhammad Farsya Indrawan", "M. Ridho Anwar", "Bebri Ananda Sinukaban"
    ]
    
    nama = st.selectbox("Pilih Nama", daftar_nama)
    foto = st.camera_input("Ambil Foto Wajah")

    if st.button("Kirim Absen"):
        if foto is not None:
            with st.spinner("Sedang mengirim data ke Google Sheets..."):
                try:
                    # A. Upload ke ImgBB
                    files = {"image": foto.getvalue()}
                    resp = requests.post(f"https://api.imgbb.com/1/upload?key={API_IMGBB}", files=files)
                    link_foto = resp.json()["data"]["url"]

                    # B. Ambil data lama dari Sheets (TTL=0 agar selalu terbaru)
                    df_lama = conn.read(ttl=0).dropna(how="all")

                    # C. Tambahkan data baru
                    data_baru = pd.DataFrame([{
                        "Nama": nama,
                        "Tanggal": tgl_sekarang,
                        "Jam": jam_skrg,
                        "Foto_Link": link_foto,
                        "Preview_Foto": f'=IMAGE("{link_foto}")'
                    }])

                    df_final = pd.concat([df_lama, data_baru], ignore_index=True)

                    # D. Update kembali ke Google Sheets
                    conn.update(data=df_final)
                    
                    # Bersihkan cache agar data terbaru muncul di tab arsip
                    st.cache_data.clear()
                    st.success(f"✅ Berhasil! {nama} tercatat jam {jam_skrg} WIB.")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"Terjadi kesalahan: {e}")
        else:
            st.warning("Silakan ambil foto terlebih dahulu!")

elif menu == "🗄️ Arsip Website":
    st.header("🗄️ Arsip Data Absensi")
    try:
        # Baca data dari Sheets
        df_view = conn.read(ttl=0).dropna(how="all")
        
        if not df_view.empty:
            st.dataframe(df_view, use_container_width=True)

            # Fitur Download Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_view.to_excel(writer, index=False, sheet_name='Absensi')
            
            st.download_button(
                label="📥 Download Laporan (Excel)",
                data=output.getvalue(),
                file_name=f"Absensi_KI_{tgl_sekarang}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("Belum ada data di Google Sheets.")
    except Exception as e:
        st.error("Gagal mengambil data dari Google Sheets. Pastikan Secrets dan Izin Share sudah benar.")
