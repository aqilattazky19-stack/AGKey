import streamlit as st
import google.generativeai as genai
import requests
import json
import pandas as pd
from PIL import Image
import io
import cairosvg
import time  # <-- PENTING: Tambahkan library time untuk memberi jeda

# 1. Konfigurasi Tampilan
st.set_page_config(page_title="Global Microstock SEO Generator", page_icon="📸", layout="wide")

st.title("📸 Global Microstock SEO & Metadata Generator")
st.caption("Batch Upload dengan fitur Anti-Rate Limit untuk API Gratis.")

# 2. Input API Key
st.sidebar.header("Pengaturan API")
api_key_input = st.sidebar.text_input("Masukkan Gemini API Key Anda:", type="password")
st.sidebar.markdown("[Dapatkan API Key Gratis di Sini](https://aistudio.google.com/)")

def get_global_trends(keyword):
    try:
        url = f"http://suggestqueries.google.com/complete/search?client=chrome&q={keyword}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()[1]
    except:
        return []
    return []

# 3. Fitur Utama
if not api_key_input:
    st.info("💡 Silakan masukkan Gemini API Key Anda di bilah samping (sidebar) untuk mulai!")
else:
    genai.configure(api_key=api_key_input)
    
    uploaded_files = st.file_uploader(
        "Unggah foto, ilustrasi, atau file vektor Anda (Bisa pilih banyak)", 
        type=["jpg", "jpeg", "png", "svg"], 
        accept_multiple_files=True
    )
    
    if uploaded_files:
        st.write(f"📁 **{len(uploaded_files)} file siap diproses.**")
        
        if st.button("Proses Semua Gambar (Aman Kuota) 🚀", type="primary"):
            all_results = [] 
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for index, uploaded_file in enumerate(uploaded_files):
                file_ext = uploaded_file.name.split(".")[-1].lower()
                status_text.text(f"Menganalisis ({index+1}/{len(uploaded_files)}): {uploaded_file.name}...")
                
                # Skenario Anti-Gagal: Coba proses, jika kena limit, tunggu dan coba lagi
                sukses = False
                percobaan = 0
                
                while not sukses and percobaan < 3:
                    try:
                        if file_ext == "svg":
                            svg_bytes = uploaded_file.read()
                            png_bytes = cairosvg.svg2png(bytestring=svg_bytes)
                            image = Image.open(io.BytesIO(png_bytes))
                            uploaded_file.seek(0) # Reset pointer file agar bisa dibaca lagi kalau gagal
                        else:
                            image = Image.open(uploaded_file)
                        
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        prompt_analysis = (
                            "Analyze this image for commercial microstock platforms. "
                            "Provide: 1. A catchy, SEO-friendly Title (max 70 chars). "
                            "2. Top 3 primary core keywords describing the image. "
                            "3. A Category recommendation. "
                            "Respond STRICTLY in JSON format: {\"title\": \"\", \"core_keywords\": [], \"category\": \"\"}"
                        )
                        
                        # Request ke API
                        response = model.generate_content([prompt_analysis, image])
                        clean_text = response.text.strip().replace("```json", "").replace("```", "")
                        result = json.loads(clean_text)
                        
                        core_keyword = result["core_keywords"][0] if result["core_keywords"] else "stock photo"
                        trends = get_global_trends(core_keyword)
                        
                        prompt_keywords = f"Given core keywords: {', '.join(result['core_keywords'])} and these global search trends: {', '.join(trends)}. Generate exactly 45 highly relevant microstock tags/keywords separated by commas. Focus on global buyers."
                        
                        # Request kedua ke API
                        keywords_response = model.generate_content(prompt_keywords)
                        keywords_text = keywords_response.text.strip()
                        
                        all_results.append({
                            'Filename': uploaded_file.name,
                            'Title': result["title"],
                            'Keywords': keywords_text
                        })
                        
                        sukses = True # Berhasil diproses, keluar dari perulangan while
                        
                        # Beri jeda 15 detik sebelum gambar selanjutnya agar tidak ditandai spam oleh Google
                        if index < len(uploaded_files) - 1:
                            status_text.text(f"⏳ Berhasil! Menjaga batas kuota gratis API. Menunggu 15 detik sebelum gambar berikutnya...")
                            time.sleep(15)
                            
                    except Exception as e:
                        error_msg = str(e)
                        if "429" in error_msg or "Quota exceeded" in error_msg:
                            percobaan += 1
                            status_text.warning(f"⚠️ Kuota API per menit penuh. Menunggu 60 detik sebelum melanjutkan {uploaded_file.name} (Percobaan ulang {percobaan}/3)...")
                            time.sleep(60) # Tunggu 1 menit sesuai instruksi error Google
                        else:
                            st.error(f"Gagal memproses {uploaded_file.name}: {error_msg}")
                            break # Hentikan kalau errornya bukan karena limit
                
                # Update bar progres
                progress_bar.progress((index + 1) / len(uploaded_files))
            
            status_text.success("✅ Selesai memproses semua file!")
            
            if all_results:
                st.session_state['batch_csv_data'] = pd.DataFrame(all_results)
        
        if 'batch_csv_data' in st.session_state:
            df_result = st.session_state['batch_csv_data']
            st.markdown("---")
            st.subheader("📊 Hasil Batch Metadata")
            st.dataframe(df_result, use_container_width=True)
            
            csv_bytes = df_result.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download CSV Batch Adobe Stock",
                data=csv_bytes,
                file_name="adobe_stock_batch_metadata.csv",
                mime='text/csv',
                use_container_width=True
            )
