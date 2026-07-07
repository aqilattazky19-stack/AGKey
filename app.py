import streamlit as st
import google.generativeai as genai
import requests
import json
from PIL import Image

# 1. Konfigurasi Tampilan Halaman Website
st.set_page_config(page_title="Global Microstock SEO Generator", page_icon="📸", layout="wide")

st.title("📸 Global Microstock SEO & Metadata Generator")
st.caption("Tanpa batasan penggunaan. Akurat berdasarkan tren pasar global.")

# 2. Input API Key (Agar Pengguna Bisa Pakai Tanpa Batas)
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
    st.info("💡 Silakan masukkan Gemini API Key Anda di bilah samping (sidebar) untuk mulai menggunakan aplikasi tanpa batasan!")
else:
    # Konfigurasi AI dengan API Key yang dimasukkan pengguna
    genai.configure(api_key=api_key_input)
    
    # Area Unggah Gambar
    uploaded_file = st.file_uploader("Unggah foto atau ilustrasi Anda (JPG/PNG)", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        
        # Tampilkan Kolom Kiri (Gambar) dan Kolom Kanan (Hasil)
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.image(image, caption="Preview Gambar", use_container_width=True)
            
        with col2:
            st.subheader("Hasil Optimasi Metadata")
            
            if st.button("Generate Metadata 🚀", type="primary"):
                with st.spinner("Menganalisis gambar & tren pasar global..."):
                    try:
                        # Inisialisasi Model AI Vision
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        
                        # Prompt Tahap 1: Analisis Gambar
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
                        
                        # Prompt Tahap 2: Menghasilkan 40-50 Keywords Komersial
                        prompt_keywords = f"Given core keywords: {', '.join(result['core_keywords'])} and these global search trends: {', '.join(trends)}. Generate exactly 45 highly relevant microstock tags/keywords separated by commas. Focus on global buyers."
                        keywords_response = model.generate_content(prompt_keywords)
                        
                        # Tampilkan Hasil ke UI Website
                        st.text_input("🏷️ Kategori Disarankan", value=result["category"])
                        st.text_input("📝 Judul SEO Global", value=result["title"])
                        
                        keywords_text = keywords_response.text.strip()
                        st.text_area("🔑 Keywords / Tags (Siap Copy-Paste)", value=keywords_text, height=150)
                        
                        st.success("Metadata berhasil dibuat! Anda tinggal menyalinnya ke dasbor Adobe Stock / Shutterstock.")
                        
                    except Exception as e:
                        st.error(f"Terjadi kesalahan: {e}. Pastikan API Key Anda valid.")