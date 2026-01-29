import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
import os
import requests
from fpdf import FPDF
import plotly.graph_objects as go
from datetime import datetime
import base64

# --- 1. CONFIGURATION & ASSETS ---
st.set_page_config(page_title="Agri-Smart Ecosystem (A.S.E)", layout="wide", page_icon="🌾")

# Placeholder API Key (OpenWeatherMap)
API_KEY = "44ce6d6e018ff31baf4081ed56eb7fb7" 

# --- 2. MULTI-LINGUAL KNOWLEDGE BASE (Simulating Online Resources) ---
# In a real app, this would fetch from a database or Google Custom Search API
KNOWLEDGE_BASE = {
    "Wheat": {
        "English": {
            "Climate": "Cool winters (10-15°C) and warm summers.",
            "Soil": "Well-drained Loam or Clay Loam.",
            "Water": "Requires 4-6 irrigations at critical stages.",
            "Fertilizer": "NPK Ratio: 4:2:1. Add Urea at crown root initiation."
        },
        "Hindi": {
            "Climate": "ठंडी सर्दियाँ (10-15°C) और गर्म ग्रीष्मकाल।",
            "Soil": "अच्छी जल निकासी वाली दोमट या चिकनी मिट्टी।",
            "Water": "महत्वपूर्ण चरणों में 4-6 सिंचाई की आवश्यकता होती है।",
            "Fertilizer": "NPK अनुपात: 4:2:1। जड़ बनते समय यूरिया डालें।"
        }
    },
    "Rice": {
        "English": {
            "Climate": "Hot and humid (20-35°C). High rainfall.",
            "Soil": "Clayey soil with good water retention.",
            "Water": "Requires standing water (submergence).",
            "Fertilizer": "Bio-fertilizers like Azolla enhance yield."
        },
        "Hindi": {
            "Climate": "गर्म और आर्द्र (20-35°C)। अधिक वर्षा।",
            "Soil": "पानी रोकने वाली चिकनी मिट्टी।",
            "Water": "खड़े पानी (जलमग्नता) की आवश्यकता होती है।",
            "Fertilizer": "एजोला जैसे जैव उर्वरक उपज बढ़ाते हैं।"
        }
    },
    "Maize": {
        "English": {
            "Climate": "Warm weather, cannot tolerate frost.",
            "Soil": "Deep, fertile, well-drained soils.",
            "Water": "Sensitive to both drought and waterlogging.",
            "Fertilizer": "Needs high Nitrogen application."
        },
        "Hindi": {
            "Climate": "गर्म मौसम, पाला सहन नहीं कर सकता।",
            "Soil": "गहरी, उपजाऊ, अच्छी जल निकासी वाली मिट्टी।",
            "Water": "सूखा और जलभराव दोनों के प्रति संवेदनशील।",
            "Fertilizer": "उच्च नाइट्रोजन आवेदन की आवश्यकता है।"
        }
    }
}

LANG_DICT = {
    "English": {
        "title": "Agri-Smart Dashboard",
        "weather": "Live Weather & Forecast",
        "soil_step": "Step 1: Visual Soil Selection",
        "report": "Analysis & PDF Report",
        "rental": "Equipment Rental (Click to Call/SMS)",
        "knowledge": "Crop Knowledge Center",
        "rain_alert": "⚠️ ALERT: Rain Predicted! Delay fertilizer application.",
        "clear_alert": "✅ SAFE: Weather is clear for fertilizer.",
        "download": "📥 Download Farmer Report",
    },
    "Hindi": {
        "title": "एग्री-स्मार्ट डैशबोर्ड",
        "weather": "लाइव मौसम और पूर्वानुमान",
        "soil_step": "चरण 1: मिट्टी का चयन",
        "report": "विश्लेषण और पीडीएफ रिपोर्ट",
        "rental": "कृषि उपकरण किराया (कॉल/SMS करें)",
        "knowledge": "फसल ज्ञान केंद्र",
        "rain_alert": "⚠️ चेतावनी: बारिश की संभावना! आज खाद न डालें।",
        "clear_alert": "✅ सुरक्षित: मौसम साफ है। उर्वरक डाल सकते हैं।",
        "download": "📥 किसान रिपोर्ट डाउनलोड करें",
    }
}

# --- 3. PDF GENERATION ENGINE ---
class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Agri-Smart Ecosystem - Farmer Report', 0, 1, 'C')
        self.ln(5)

    def generate_content(self, user, city, soil_type, scores, weather_data):
        self.set_font('Arial', '', 12)
        # Farmer Details
        self.set_fill_color(230, 240, 230)
        self.cell(0, 10, f"Farmer Name: {user} | Location: {city}", 0, 1, 'L', True)
        self.cell(0, 10, f"Date: {datetime.now().strftime('%d-%m-%Y')} | Soil Type: {soil_type}", 0, 1, 'L', True)
        self.ln(10)
        
        # Weather Section
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, "1. Current Weather Status", 0, 1)
        self.set_font('Arial', '', 12)
        if weather_data:
            self.cell(0, 10, f"Temp: {weather_data['main']['temp']}C | Humidity: {weather_data['main']['humidity']}%", 0, 1)
            self.cell(0, 10, f"Condition: {weather_data['weather'][0]['description']}", 0, 1)
        self.ln(5)

        # Crop Section
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, "2. Recommended Crops (Suitability Score)", 0, 1)
        self.set_font('Arial', '', 12)
        for crop, score in scores.items():
            self.cell(0, 10, f"- {crop}: {round(score*100, 1)}%", 0, 1)
        
        # Disclaimer
        self.ln(20)
        self.set_font('Arial', 'I', 10)
        self.multi_cell(0, 10, "Note: This report is generated by AI based on visual soil inputs. Please consult a lab for chemical testing before large investments.")

# --- 4. UTILITIES ---
def get_weather(city):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        return requests.get(url).json()
    except: return None

def calculate_suitability(vec):
    crops_db = {
        "Wheat": np.array([80, 40, 40, 20]),
        "Rice": np.array([100, 60, 40, 80]),
        "Maize": np.array([60, 30, 30, 40])
    }
    return {c: np.dot(vec, t)/(np.linalg.norm(vec)*np.linalg.norm(t)) for c, t in crops_db.items()}

# --- 5. MAIN APP ---
if 'authenticated' not in st.session_state: st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🚜 Agri-Smart Secure Login")
    c1, c2 = st.columns(2)
    with c1:
        u = st.text_input("Username (e.g., kisan1)")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            st.session_state.authenticated = True
            st.session_state.user = u
            st.rerun()
else:
    # Sidebar
    lang = st.sidebar.radio("Select Language", ["English", "Hindi"], horizontal=True)
    T = LANG_DICT[lang]
    city = st.sidebar.text_input("City/Village", "Patna")
    st.sidebar.markdown("---")
    
    st.title(f"🌾 {T['title']}")
    
    # --- A. LIVE WEATHER ---
    w = get_weather(city)
    if w and 'main' in w:
        c1, c2, c3 = st.columns(3)
        c1.metric("🌡 Temp", f"{w['main']['temp']}°C")
        c2.metric("💧 Humidity", f"{w['main']['humidity']}%")
        c3.metric("☁ Condition", w['weather'][0]['main'])
        
        is_raining = "rain" in w['weather'][0]['description'].lower()
        if is_raining: st.error(T['rain_alert'])
        else: st.success(T['clear_alert'])
    
    # --- B. VISUAL SOIL SELECTION ---
    st.header(T['soil_step'])
    cols = st.columns(3)
    soils = [
        {"n": "Alluvial", "v": [90,50,45,30], "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Soil_profile.jpg/640px-Soil_profile.jpg"},
        {"n": "Black", "v": [70,40,60,50], "img": "https://upload.wikimedia.org/wikipedia/commons/2/23/Black_Soil.jpg"},
        {"n": "Clay", "v": [50,30,30,70], "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/02/Clay-ss-2005.jpg/640px-Clay-ss-2005.jpg"}
    ]
    
    for idx, s in enumerate(soils):
        with cols[idx]:
            st.image(s['img'], height=150, use_container_width=True)
            if st.button(f"Select {s['n']}", key=idx):
                st.session_state.soil_vec = s['v']
                st.session_state.soil_name = s['n']

    # --- C. ANALYSIS, REPORT & KNOWLEDGE ---
    if 'soil_vec' in st.session_state:
        st.divider()
        scores = calculate_suitability(np.array(st.session_state.soil_vec))
        
        col_res, col_know = st.columns([1, 1])
        
        with col_res:
            st.subheader(f"📊 {T['report']}")
            for crop, score in scores.items():
                st.write(f"**{crop}**")
                st.progress(score)
            
            # PDF Generation
            pdf = PDFReport()
            pdf.add_page()
            pdf.generate_content(st.session_state.user, city, st.session_state.soil_name, scores, w)
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            st.download_button(label=T['download'], data=pdf_bytes, file_name=f"Soil_Report_{st.session_state.user}.pdf", mime='application/pdf')

        with col_know:
            st.subheader(f"🧠 {T['knowledge']}")
            selected_crop = st.selectbox("Select Crop for Details / फसल चुनें", ["Wheat", "Rice", "Maize"])
            info = KNOWLEDGE_BASE[selected_crop][lang]
            with st.chat_message("assistant"):
                st.markdown(f"**Climate:** {info['Climate']}")
                st.markdown(f"**Soil Prep:** {info['Soil']}")
                st.markdown(f"**Water:** {info['Water']}")
                st.markdown(f"**Fertilizer:** {info['Fertilizer']}")

    # --- D. RENTAL MARKETPLACE (CALL/SMS) ---
    st.divider()
    st.header(f"🚜 {T['rental']}")
    
    rentals = [
        {"name": "Mahindra Tractor", "price": "₹600/hr", "owner": "Raju Bhai", "ph": "9876543210", "img": "https://cdn-icons-png.flaticon.com/512/2674/2674486.png"},
        {"name": "Rotavator", "price": "₹200/hr", "owner": "Kisan Seva", "ph": "9123456789", "img": "https://cdn-icons-png.flaticon.com/512/3600/3600986.png"},
        {"name": "Harvester", "price": "₹1200/hr", "owner": "Amit Singh", "ph": "9988776655", "img": "https://cdn-icons-png.flaticon.com/512/5753/5753966.png"}
    ]
    
    r1, r2, r3 = st.columns(3)
    for idx, (col, item) in enumerate(zip([r1, r2, r3], rentals)):
        with col:
            st.image(item['img'], width=80)
            st.write(f"**{item['name']}**")
            st.caption(f"Price: {item['price']} | Owner: {item['owner']}")
            
            # Call & SMS Links
            c_btn, s_btn = st.columns(2)
            c_btn.markdown(f'<a href="tel:{item["ph"]}" style="text-decoration:none;"><button style="width:100%; background-color:#4CAF50; color:white; border:none; padding:5px; border-radius:5px;">📞 Call</button></a>', unsafe_allow_html=True)
            s_btn.markdown(f'<a href="sms:{item["ph"]}?body=I need {item["name"]} on rent." style="text-decoration:none;"><button style="width:100%; background-color:#2196F3; color:white; border:none; padding:5px; border-radius:5px;">💬 SMS</button></a>', unsafe_allow_html=True)

    st.sidebar.button("Logout", on_click=lambda: st.session_state.clear())
