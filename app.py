import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
import os
import requests
from fpdf import FPDF

# --- 1. SYSTEM CONFIGURATION ---
st.set_page_config(page_title="Agri-Smart Ecosystem", layout="wide")

API_KEY = "44ce6d6e018ff31baf4081ed56eb7fb7"

LANG_DICT = {
    "English": {
        "title": "Agri-Smart Ecosystem",
        "weather": "Live Weather Analytics",
        "soil_step": "Step 1: Visual Soil Selection",
        "report": "Smart Soil Report",
        "schemes": "Integrated Knowledge Hub",
        "contact": "Hybrid Resource Connectivity"
    },
    "Hindi": {
        "title": "एग्री-स्मार्ट इकोसिस्टम",
        "weather": "लाइव मौसम विश्लेषण",
        "soil_step": "चरण 1: मिट्टी का दृश्य चयन",
        "report": "स्मार्ट मिट्टी रिपोर्ट",
        "schemes": "एकीकृत ज्ञान केंद्र",
        "contact": "हाइब्रिड संसाधन कनेक्टिविटी"
    }
}

# --- 2. SUPPORT FUNCTIONS ---

def get_weather(city):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        response = requests.get(url).json()
        return response
    except:
        return None

def create_pdf(user, soil_name, scores):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="A.S.E - Precision Farming Soil Report", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Farmer Name: {user}", ln=True)
    pdf.cell(200, 10, txt=f"Primary Soil Type: {soil_name}", ln=True)
    pdf.cell(200, 10, txt="----------------------------------------------------------", ln=True)
    for crop, score in scores.items():
        pdf.cell(200, 10, txt=f"- {crop}: {round(score*100, 2)}% Match", ln=True)
    return pdf.output(dest='S').encode('latin-1')

def calculate_suitability(vec):
    crops_db = {
        "Wheat": np.array([80, 40, 40, 20]),
        "Rice": np.array([100, 60, 40, 80]),
        "Maize": np.array([60, 30, 30, 40])
    }
    results = {}
    for crop, target in crops_db.items():
        score = np.dot(vec, target) / (np.linalg.norm(vec) * np.linalg.norm(target))
        results[crop] = score
    return results

# --- 3. AUTHENTICATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 A.S.E Secure Login")
    user = st.text_input("Username / Mobile")
    passw = st.text_input("Password", type="password")
    if st.button("Login"):
        st.session_state.logged_in = True
        st.session_state.user = user
        st.rerun()
else:
    # --- 4. MAIN DASHBOARD ---
    lang = st.sidebar.selectbox("Language / भाषा", ["English", "Hindi"])
    T = LANG_DICT[lang]
    city = st.sidebar.text_input("Your District", "Patna")
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    st.title(f"🌾 {T['title']}")

    # --- WEATHER & SMART ALERT SECTION ---
    w_data = get_weather(city)
    if w_data and w_data.get("main"):
        st.info(f"☀️ {T['weather']}: {city} | Temp: {w_data['main']['temp']}°C | Humid: {w_data['main']['humidity']}%")
        
        weather_desc = w_data['weather'][0]['description'].lower()
        if "rain" in weather_desc or "drizzle" in weather_desc:
            st.error("⚠️ **CRITICAL ALERT / महत्वपूर्ण सूचना**")
            st.write("📢 **English:** It is likely to rain. **DO NOT** apply fertilizer today.")
            st.write("📢 **हिंदी:** आज बारिश की संभावना है। कृपया आज **उर्वरक (खाद)** न डालें।")
        else:
            st.success("✅ Weather is clear for fertilizer application.")

    # --- STEP 1: SAFE SOIL SELECTION (ADD IT HERE) ---
    st.header(T['soil_step'])
    col1, col2, col3 = st.columns(3)

    soil_list = [
        {"name": "Alluvial", "vec": [90, 50, 45, 30], "img": "assets/alluvial.jpg", "c": col1},
        {"name": "Black", "vec": [70, 40, 60, 50], "img": "assets/black.jpg", "c": col2},
        {"name": "Clay", "vec": [50, 30, 30, 70], "img": "assets/clay.jpg", "c": col3}
    ]

    for s in soil_list:
        with s["c"]:
            if os.path.exists(s["img"]):
                st.image(Image.open(s["img"]), use_container_width=True)
            else:
                st.error(f"Missing: {s['img']}")
                st.info("Check your 'assets' folder on GitHub.")
                
            if st.button(f"Select {s['name']}"):
                st.session_state.soil_vec = s["vec"]
                st.session_state.soil_name = s["name"]

    # --- STEP 2: ANALYSIS & REPORT ---
    if 'soil_vec' in st.session_state:
        st.divider()
        st.header(f"📊 {T['report']}: {st.session_state.soil_name}")
        c_an, c_kn = st.columns(2)
        
        with c_an:
            scores = calculate_suitability(np.array(st.session_state.soil_vec))
            for crop, score in scores.items():
                st.write(f"**{crop}**: {round(score*100, 2)}%")
                st.progress(score)
            
            pdf_bytes = create_pdf(st.session_state.user, st.session_state.soil_name, scores)
            st.download_button("📥 Download Soil Report PDF", data=pdf_bytes, file_name="Soil_Report.pdf")

        with c_kn:
            st.subheader(f"📋 {T['schemes']}")
            # Path checking for schemes
            if os.path.exists("data/schemes.csv"):
                st.dataframe(pd.read_csv("data/schemes.csv"), hide_index=True)
            else:
                st.error("File 'data/schemes.csv' not found.")

    st.divider()
    st.header(f"📞 {T['contact']}")
    st.button("📲 One-Tap Call: Regional Rental Center")
