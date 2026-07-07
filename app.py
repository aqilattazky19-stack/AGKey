import streamlit as st
import google.generativeai as genai
import requests
import json
import pandas as pd
from PIL import Image
import io
import cairosvg

# 1. Konfigurasi Tampilan Halaman Website
st.set_page_config(page_title="Global Microstock SEO Generator", page_icon="📸", layout="wide")

st.title("📸 Global Microstock SEO & Metadata Generator (Batch Mode)")
st.caption("Mendukung Batch Upload (JPG, PNG, SVG sekaligus). Tanpa batasan penggunaan.")

# 2. Input API Key di Sidebar
st.sidebar.header("Pengaturan API")
api_key_input = st.sidebar.text_input("Masukkan Gemini API Key Anda:", type="password")
st.sidebar.markdown("[Dapatkan API Key Gratis di Sini](https://aistudio.google.com/)")

# Fungsi untuk mengambil tren pasar global (Google Autocomplete)
def get_global_trends(keyword):
    try:
        url = f"http://suggestqueries.google.com/complete/search?client=chrome&q={keyword}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()[1]
    except:
        return []
    return []

# 3. Fitur Utama Website
if not api_key_input:
    st.info("💡 Silakan masukkan Gemini API Key Anda di bilah samping (sidebar) untuk mulai menggunakan aplikasi!")
else:
    genai.configure(api_key=api_key_input)
    
    # AKTIFKAN BATCH UPLOAD DI SINI (accept_multiple_files=True)
    uploaded_files = st.file_uploader(
        "Unggah foto, ilustrasi, atau file vektor Anda (Bisa pilih banyak file sekaligus)", 
        type=["jpg", "jpeg", "png", "svg"], 
        accept_multiple_files=True
    )
    
    # Jika ada file yang diunggah
    if uploaded_files:
        st.write(f"📁 **{len(uploaded_files)} file siap diproses.**")
        
        # Tombol untuk mulai memproses seluruh gambar secara massal
        if st.button("Proses Semua Gambar massal 🚀", type="primary"):
            all_results = [] # Tempat menampung data CSV gabungan
            
            # Progress bar untuk memantau status pengerjaan
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Lakukan perulangan untuk setiap file yang diunggah
            for index, uploaded_file in enumerate(uploaded_files):
                file_ext = uploaded_file.name.split(".")[-1].lower()
                status_text.text(f"Memproses ({index+1}/{len(uploaded_files)}): {uploaded_file.name}...")
                
                try:
                    # Baca gambar (jika SVG, konversi dulu ke PNG untuk AI)
                    if file_ext == "svg":
                        svg_bytes = uploaded_file.read()
                        png_bytes = cairosvg.svg2png(bytestring=svg_bytes)
                        image = Image.open(io.BytesIO(png_bytes))
                    else:
                        image = Image.open(uploaded_file)
                    
                    # Hubungi AI Gemini
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    prompt_analysis = (
                        "Analyze this image for commercial microstock platforms. "
                        "Provide: 1. A catchy, SEO-friendly Title (max 70 chars). "
                        "2. Top 3 primary core keywords describing the image. "
                        "3. A Category recommendation. "
                        "Respond STRICTLY in JSON format: {\"title\": \"\", \"core_keywords\": [], \"category\": \"\"}"
                    )
                    
                    response = model.generate_content([prompt_analysis, image])
                    clean_text = response.text.strip().replace("```json", "").replace("```", "")
                    result = json.loads(clean_text)
                    
                    # Ambil Tren Global & Tambah Keywords
                    core_keyword = result["core_keywords"][0] if result["core_keywords"] else "stock photo"
                    trends = get_global_trends(core_keyword)
                    
                    prompt_keywords = f"Given core keywords: {', '.join(result['core_keywords'])} and these global search trends: {', '.join(trends)}. Generate exactly 45 highly relevant microstock tags/keywords separated by commas. Focus on global buyers."
                    keywords_response = model.generate_content(prompt_keywords)
                    keywords_text = keywords_response.text.strip()
                    
                    # Masukkan data ke dalam list gabungan
                    all_results.append({
                        'Filename': uploaded_file.name,
                        'Title': result["title"],
                        'Keywords': keywords_text
                    })
                    
                except Exception as e:
                    st.warning(f"Gagal memproses {uploaded_file.name}: {e}")
                
                # Update progress bar
                progress_bar.progress((index + 1) / len(uploaded_files))
            
            status_text.text("✅ Selesai memproses semua file!")
            
            # Jika ada hasil yang sukses, buatkan satu file CSV gabungan
            if all_results:
                st.session_state['batch_csv_data'] = pd.DataFrame(all_results)
        
        # Tampilkan hasil download jika data batch sudah selesai diproses
        if 'batch_csv_data' in st.session_state:
            df_result = st.session_state['batch_csv_data']
            
            st.markdown("---")
            st.subheader("📊 Hasil Batch Metadata")
            st.dataframe(df_result, use_container_width=True) # Tampilkan tabel pratinjau hasil
            
            # Buat tombol download untuk 1 file CSV tunggal isi semua gambar
            csv_bytes = df_result.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download 1 File CSV Gabungan (Untuk Semua Gambar)",
                data=csv_bytes,
                file_name="adobe_stock_batch_metadata.csv",
                mime='text/csv',
                use_container_width=True
            )
            st.success("Selesai! Sekarang Anda cukup unggah 1 file CSV ini ke Adobe Stock, dan semua gambar Anda akan langsung terisi metadatanya secara otomatis.")
