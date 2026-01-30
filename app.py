import streamlit as st
import numpy as np
import requests
import pandas as pd
import random
from fpdf import FPDF
from datetime import datetime
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go

# --- CONFIGURATION & API ---
st.set_page_config(page_title="Agri-Smart Ecosystem (A.S.E)", layout="wide", page_icon="🌾")
API_KEY = "44ce6d6e018ff31baf4081ed56eb7fb7" 

# --- DATA ENGINES ---
CENTRAL_SCHEMES = [
    {"Scheme": "PM-KISAN", "Benefit": "₹2,000 (22nd Installment Feb 2026)", "Link": "https://pmkisan.gov.in/"},
    {"Scheme": "PM-KUSUM 2.0", "Benefit": "Solar Pump Subsidy (Up to 50%)", "Link": "https://pmkusum.mnre.gov.in/"}
]

STATE_SCHEMES = {
    "Bihar": [{"Scheme": "Bihar Rajya Fasal Sahayata", "Benefit": "Crop Loss Support", "Link": "https://pacsonline.bih.nic.in/"}],
    "Maharashtra": [{"Scheme": "Namo Shetkari Yojana", "Benefit": "Addl. ₹6,000/year", "Link": "https://nsmny.maharashtra.gov.in/"}],
    "Punjab": [{"Scheme": "CRM Scheme", "Benefit": "Happy Seeder Subsidy", "Link": "https://agrimachinery.nic.in/"}]
}

DISEASE_DB = {
    "Wheat": {"yellow leaves": "Yellow Rust (Fix: Propiconazole)", "brown spots": "Leaf Blight (Fix: Mancozeb)"},
    "Rice": {"wilting": "Bacterial Blight (Fix: Streptocycline)", "holes": "Stem Borer (Fix: Carbofuran)"}
}

# --- FUNCTIONS ---
def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    try:
        r = requests.get(url, timeout=5).json()
        return {"temp": r['main']['temp'], "hum": r['main']['humidity'], "desc": r['weather'][0]['description']}
    except: return {"temp": 25, "hum": 60, "desc": "API Offline (Demo Mode)"}

def create_pdf(farmer, city, soil, scores):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "OFFICIAL AGRI-SMART REPORT 2026", ln=1, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Farmer: {farmer} | Location: {city} | Date: {datetime.now().date()}", ln=1)
    pdf.cell(0, 10, f"Soil Type: {soil}", ln=1)
    for crop, s in scores.items():
        pdf.cell(0, 10, f"- {crop}: {s}% Match", ln=1)
    return pdf.output(dest='S').encode('latin-1')

# --- AUTHENTICATION ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title("🚜 Agri-Smart Login")
    name = st.text_input("Farmer Name")
    if st.button("Enter Dashboard") and name:
        st.session_state.auth, st.session_state.user = True, name
        st.rerun()
else:
    # --- UI LAYOUT ---
    dist = st.sidebar.text_input("District", "Patna").strip().title()
    lang = st.sidebar.radio("Language", ["English", "Hindi"])
    w = get_weather(dist)
    
    st.title(f"🌾 A.S.E Dashboard | Welcome {st.session_state.user}")
    
    # 1. WEATHER & GPS
    col_w, col_g = st.columns([1, 1])
    with col_w:
        st.subheader("🌦 Live Weather")
        st.metric("Temperature", f"{w['temp']}°C")
        if "rain" in w['desc'].lower(): st.error(f"⚠️ {w['desc'].title()}: Avoid Fertilizers!")
        else: st.success(f"✅ {w['desc'].title()}: Good for spraying.")
    
    with col_g:
        st.subheader("📍 Field Mapping")
        m = folium.Map(location=[25.59, 85.13], zoom_start=12)
        folium.Marker([25.59, 85.13], tooltip="Your Field").add_to(m)
        st_folium(m, height=150, use_container_width=True)

    # 2. CORE FEATURES TABS
    t1, t2, t3, t4 = st.tabs(["Soil & Fertilizer", "Pest Diagnosis", "Mandi Rates", "Live Schemes"])
    
    with t1:
        st.header("🧪 Soil & Fertilizer")
        soil_type = st.selectbox("Select Soil", ["Alluvial", "Black", "Clay"])
        acres = st.number_input("Field Size (Acres)", 0.5, 50.0, 1.0)
        crop_sel = st.selectbox("Crop", ["Wheat", "Rice", "Maize"])
        scores = {"Wheat": 85, "Rice": 70, "Maize": 65}
        
        st.write(f"**Urea Needed:** {round(acres * 1.5, 1)} Bags (50kg)")
        
        
        pdf_bytes = create_pdf(st.session_state.user, dist, soil_type, scores)
        st.download_button("📥 Download Soil Report", pdf_bytes, "Soil_Report.pdf")

    with t2:
        st.header("🦠 Symptom Checker")
        symp = st.text_input("Describe problem (e.g. yellow leaves)")
        if symp:
            res = DISEASE_DB.get(crop_sel, {}).get(symp.lower(), "Contact KVK Expert.")
            st.warning(f"Diagnosis: {res}")
        

    with t3:
        st.header("📈 Market Trends")
        prices = [2100 + random.randint(-40, 60) for _ in range(7)]
        fig = go.Figure(go.Scatter(y=prices, mode='lines+markers', line_color='green'))
        st.plotly_chart(fig, use_container_width=True)
        st.write(f"Today's Price: ₹{prices[-1]}/quintal")

    with t4:
        st.header("🏛 Live Government Schemes")
        st.subheader("Central Schemes")
        st.table(pd.DataFrame(CENTRAL_SCHEMES))
        
        state = "Bihar" if dist in ["Patna", "Gaya"] else "Other"
        if state in STATE_SCHEMES:
            st.subheader(f"{state} Specific Schemes")
            st.table(pd.DataFrame(STATE_SCHEMES[state]))
        

    # 3. RENTAL CONNECT
    st.divider()
    st.subheader("🚜 Rental Marketplace")
    st.markdown('📞 [Call Tractor Owner](tel:9876543210) | 💬 [SMS Request](sms:9876543210?body=Need help at my field)')
