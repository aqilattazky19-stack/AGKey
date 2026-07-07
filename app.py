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

st.title("📸 Global Microstock SEO & Metadata Generator (Standard v2)")
st.caption("Mendukung JPG, PNG, SVG. Tanpa batasan penggunaan & Akurat sesuai pasar global.")

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
    # Konfigurasi AI dengan API Key yang dimasukkan pengguna
    genai.configure(api_key=api_key_input)
    
    # Area Unggah Gambar (Sekarang Mendukung SVG)
    uploaded_file = st.file_uploader("Unggah foto, ilustrasi, atau file vektor Anda (JPG, PNG, SVG)", type=["jpg", "jpeg", "png", "svg"])
    
    if uploaded_file is not None:
        file_ext = uploaded_file.name.split(".")[-1].lower()
        
        # Proses Pembacaan Gambar Berdasarkan Format
        if file_ext == "svg":
            try:
                # Konversi SVG ke PNG sementara di dalam memori agar bisa dibaca AI & ditampilkan di UI
                svg_bytes = uploaded_file.read()
                png_bytes = cairosvg.svg2png(bytestring=svg_bytes)
                image = Image.open(io.BytesIO(png_bytes))
            except Exception as e:
                st.error(f"Gagal memproses file SVG: {e}. Pastikan file SVG Anda valid.")
                st.stop()
        else:
            image = Image.open(uploaded_file)
        
        # Tampilkan Kolom Kiri (Preview) dan Kolom Kanan (Hasil)
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.image(image, caption=f"Preview Gambar ({file_ext.upper()})", use_container_width=True)
            
        with col2:
            st.subheader("Hasil Optimasi Metadata")
            
            if st.button("Generate Metadata 🚀", type="primary"):
                with st.spinner("Menganalisis gambar & tren pasar global..."):
                    try:
                        # Inisialisasi Model AI Vision
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        
                        # Prompt Analisis Gambar
                        prompt_analysis = (
                            "Analyze this image for commercial microstock platforms. "
                            "Provide: 1. A catchy, SEO-friendly Title (max 70 chars). "
                            "2. Top 3 primary core keywords describing the image. "
                            "3. A Category recommendation. "
                            "Respond STRICTLY in JSON format: {\"title\": \"\", \"core_keywords\": [], \"category\": \"\"}"
                        )
                        
                        response = model.generate_content([prompt_analysis, image])
                        
                        # Bersihkan & Parsing JSON dari AI
                        clean_text = response.text.strip().replace("```json", "").replace("```", "")
                        result = json.loads(clean_text)
                        
                        # Ambil Tren Global Berdasarkan Core Keyword
                        core_keyword = result["core_keywords"][0] if result["core_keywords"] else "stock photo"
                        trends = get_global_trends(core_keyword)
                        
                        # Menghasilkan 45 Keywords Komersial
                        prompt_keywords = f"Given core keywords: {', '.join(result['core_keywords'])} and these global search trends: {', '.join(trends)}. Generate exactly 45 highly relevant microstock tags/keywords separated by commas. Focus on global buyers."
                        keywords_response = model.generate_content(prompt_keywords)
                        keywords_text = keywords_response.text.strip()
                        
                        # Menyimpan hasil sementara ke session_state agar tidak hilang saat tombol unduh diklik
                        st.session_state['metadata_result'] = {
                            'filename': uploaded_file.name,
                            'category': result["category"],
                            'title': result["title"],
                            'keywords': keywords_text
                        }
                        
                    except Exception as e:
                        st.error(f"Terjadi kesalahan AI: {e}. Periksa kembali API Key Anda.")
            
            # Jika metadata sudah pernah di-generate, tampilkan hasilnya
            if 'metadata_result' in st.session_state:
                res_data = st.session_state['metadata_result']
                
                title_val = st.text_input("📝 Judul SEO Global", value=res_data['title'])
                keywords_val = st.text_area("🔑 Keywords / Tags (Pisahkan dengan koma)", value=res_data['keywords'], height=150)
                st.text_input("🏷️ Kategori Disarankan", value=res_data['category'], disabled=True)
                
                st.markdown("---")
                st.subheader("💾 Opsi Simpan & Tempel (Adobe Stock)")
                
                # Fitur 1: File CSV Otomatis untuk Adobe Stock
                # Format CSV Adobe Stock membutuhkan kolom: Filename, Title, Keywords
                adobe_df = pd.DataFrame({
                    'Filename': [res_data['filename']],
                    'Title': [title_val],
                    'Keywords': [keywords_val]
                })
                
                csv_data = adobe_df.to_csv(index=False).encode('utf-8')
                
                st.download_button(
                    label="📥 Download Adobe Stock CSV",
                    data=csv_data,
                    file_name=f"adobe_stock_{res_data['filename'].split('.')[0]}.csv",
                    mime='text/csv',
                    use_container_width=True
                )
                
                st.caption("💡 Tips CSV: Di dasbor kontributor Adobe Stock, klik 'Upload CSV' lalu masukkan file yang Anda unduh di atas. Semua metadata gambar akan langsung terisi otomatis sekaligus!")
