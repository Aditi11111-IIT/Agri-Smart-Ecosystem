import streamlit as st
import pandas as pd
import requests
import random
from fpdf import FPDF
from datetime import datetime
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
import os

# --- 1. SETTINGS & INITIALIZATION ---
st.set_page_config(page_title="Agri-Smart 2026", layout="wide", page_icon="🌾")
API_KEY = "44ce6d6e018ff31baf4081ed56eb7fb7" 

# Persistent Expense State
if 'expenses' not in st.session_state:
    st.session_state.expenses = {"Seeds": 0, "Fertilizer": 0, "Labor": 0, "Irrigation": 0}

# --- 2. TRANSLATION DICTIONARY ---
content = {
    "English": {
        "title": "🚜 Agri-Smart Ecosystem",
        "weather": "Weather & Alerts", "soil": "Soil & Fertilizer", "pests": "Pest Care",
        "mandi": "Mandi Rates", "schemes": "Govt Schemes", "tracker": "Expense Tracker",
        "dist_lbl": "Select District", "crop_lbl": "Select Crop", "issue_lbl": "Select Issue",
        "sol_lbl": "Solution", "report_lbl": "Download PDF Report", "sync": "Sync Live Weather",
        "urea": "Urea Bags (50kg)", "add_exp": "Add ₹500 to", "total_exp": "Total Investment"
    },
    "Hindi": {
        "title": "🚜 एग्री-स्मार्ट इकोसिस्टम",
        "weather": "मौसम और अलर्ट", "soil": "मिट्टी और उर्वरक", "pests": "कीट उपचार",
        "mandi": "मंडी भाव", "schemes": "सरकारी योजनाएं", "tracker": "खर्चों का हिसाब",
        "dist_lbl": "अपना जिला चुनें", "crop_lbl": "अपनी फसल चुनें", "issue_lbl": "समस्या चुनें",
        "sol_lbl": "समाधान", "report_lbl": "रिपोर्ट डाउनलोड करें (PDF)", "sync": "ताज़ा मौसम",
        "urea": "यूरिया बोरी (50 किलो)", "add_exp": "₹500 जोड़ें:", "total_exp": "कुल निवेश"
    }
}

# --- 3. DATABASES ---
PEST_DB = {
    "Wheat (गेहूँ)": {
        "Yellow stripes (पीली धारियां)": "Yellow Rust: Spray Propiconazole 25% EC.",
        "Brown spots (भूरे धब्बे)": "Leaf Blight: Use Mancozeb 75 WP."
    },
    "Rice (धान)": {
        "Drying tips (पत्तियों का सूखना)": "Bacterial Blight: Apply Streptocycline.",
        "Holes in stems (तने में छेद)": "Stem Borer: Use Carbofuran 3G."
    }
}

# --- 4. CORE FUNCTIONS ---
def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    try:
        r = requests.get(url, timeout=5).json()
        return {"temp": r['main']['temp'], "desc": r['weather'][0]['description'], "hum": r['main']['humidity']}
    except: return {"temp": 28, "desc": "clear sky", "hum": 50}

def create_unicode_pdf(farmer, dist, crop, bags, total_exp):
    pdf = FPDF()
    pdf.add_page()
    # FONT CHECK
    font_path = "gargi.ttf" 
    if os.path.exists(font_path):
        pdf.add_font('HindiFont', '', font_path)
        pdf.set_font('HindiFont', size=14)
    else:
        pdf.set_font("Arial", size=12)
        
    pdf.cell(0, 10, "AGRI-SMART ECOSYSTEM REPORT 2026", ln=1, align='C')
    pdf.ln(5)
    pdf.cell(0, 10, f"Farmer: {farmer} | District: {dist}", ln=1)
    pdf.cell(0, 10, f"Crop: {crop} | Urea Required: {bags} Bags", ln=1)
    pdf.cell(0, 10, f"Total Farm Investment: Rs. {total_exp}", ln=1)
    pdf.ln(10)
    pdf.cell(0, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=1)
    
    # STREAMLIT COMPATIBILITY FIX: Return bytes
    return bytes(pdf.output())

# --- 5. APP INTERFACE ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title("🚜 A.S.E. Secure Login")
    u_name = st.text_input("Farmer Name / किसान का नाम")
    if st.button("Access Dashboard") and u_name:
        st.session_state.auth, st.session_state.user = True, u_name
        st.rerun()
else:
    lang = st.sidebar.radio("Language", ["English", "Hindi"])
    txt = content[lang]
    dist = st.sidebar.selectbox(txt["dist_lbl"], ["Patna", "Gaya", "Pune", "Ludhiana"])
    
    if st.sidebar.button(txt["sync"]):
        st.cache_data.clear()
        st.toast("Syncing Live 2026 Data...")

    w_data = get_weather(dist)
    st.title(txt["title"])
    st.write(f"👤 {st.session_state.user} | 📍 {dist}")

    tabs = st.tabs([txt["weather"], txt["soil"], txt["pests"], txt["tracker"], txt["mandi"]])

    with tabs[0]: # WEATHER & MAP
        c1, c2 = st.columns(2)
        c1.metric("Temp", f"{w_data['temp']}°C")
        c2.metric("Humidity", f"{w_data['hum']}%")
        if "rain" in w_data['desc'].lower(): st.error("⚠️ RAIN ALERT: STOP ALL SPRAYS")
        m = folium.Map(location=[25.59, 85.13], zoom_start=12)
        folium.Marker([25.59, 85.13]).add_to(m)
        st_folium(m, height=200, use_container_width=True)

    with tabs[1]: # SOIL & FERTILIZER
        st.header(txt["soil"])
        crop_sel = st.selectbox(txt["crop_lbl"], list(PEST_DB.keys()))
        acres = st.slider("Land Size (Acres)", 0.5, 50.0, 1.0)
        u_bags = round(acres * 1.5, 1)
        st.metric(txt["urea"], u_bags)
        
        
        pdf_data = create_unicode_pdf(st.session_state.user, dist, crop_sel, u_bags, sum(st.session_state.expenses.values()))
        st.download_button(txt["report_lbl"], pdf_data, "AgriReport.pdf", "application/pdf")

    with tabs[2]: # PEST DETECTION
        st.header(txt["pests"])
        issues = list(PEST_DB[crop_sel].keys())
        sel_issue = st.selectbox(txt["issue_lbl"], ["-- Select --"] + issues)
        if sel_issue != "-- Select --":
            st.warning(f"**{txt['sol_lbl']}:** {PEST_DB[crop_sel][sel_issue]}")
        

    with tabs[3]: # EXPENSE TRACKER
        st.header(txt["tracker"])
        cols = st.columns(4)
        for i, cat in enumerate(st.session_state.expenses.keys()):
            if cols[i].button(f"{txt['add_exp']} {cat}"):
                st.session_state.expenses[cat] += 500
                st.rerun() # Refresh chart immediately
        
        total = sum(st.session_state.expenses.values())
        st.subheader(f"💰 {txt['total_exp']}: ₹{total}")
        exp_df = pd.DataFrame(list(st.session_state.expenses.items()), columns=['Cat', 'Amt'])
        fig = go.Figure(data=[go.Pie(labels=exp_df['Cat'], values=exp_df['Amt'], hole=.3)])
        st.plotly_chart(fig, use_container_width=True)
        

    with tabs[4]: # MANDI
        st.header(txt["mandi"])
        prices = [2100 + random.randint(-40, 40) for _ in range(7)]
        st.line_chart(prices)

    st.divider()
    st.markdown(f'📞 [Rental Help](tel:9876543210) | 💬 [WhatsApp Support](https://wa.me/919876543210)')
