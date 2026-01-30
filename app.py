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

# --- 1. CONFIG & BILINGUAL DICTIONARY ---
st.set_page_config(page_title="Agri-Smart 2026", layout="wide", page_icon="🌾")
API_KEY = "44ce6d6e018ff31baf4081ed56eb7fb7" 

content = {
    "English": {
        "title": "🚜 Agri-Smart Ecosystem",
        "weather": "Weather & Alerts",
        "soil": "Soil & Fertilizer",
        "pests": "Pest & Disease Care",
        "mandi": "Mandi Rates",
        "schemes": "Govt Schemes",
        "district_label": "Select Your District",
        "crop_label": "Select Your Crop",
        "issue_label": "What is the problem?",
        "solution": "Recommended Solution",
        "report": "Download Soil Report (PDF)",
        "urea": "Urea Required (50kg Bags)",
        "apply": "Apply Here",
        "sync": "Sync Live Weather"
    },
    "Hindi": {
        "title": "🚜 एग्री-स्मार्ट इकोसिस्टम",
        "weather": "मौसम और अलर्ट",
        "soil": "मिट्टी और उर्वरक",
        "pests": "कीट और रोग उपचार",
        "mandi": "मंडी भाव",
        "schemes": "सरकारी योजनाएं",
        "district_label": "अपना जिला चुनें",
        "crop_label": "अपनी फसल चुनें",
        "issue_label": "समस्या क्या है?",
        "solution": "सुझाया गया समाधान",
        "report": "रिपोर्ट डाउनलोड करें (PDF)",
        "urea": "यूरिया की आवश्यकता (बोरी)",
        "apply": "यहाँ आवेदन करें",
        "sync": "ताज़ा मौसम अपडेट करें"
    }
}

# --- 2. DATABASES ---
DISTRICTS = ["Patna", "Gaya", "Muzaffarpur", "Pune", "Nagpur", "Amritsar", "Ludhiana"]

PEST_DB = {
    "Wheat (गेहूँ)": {
        "Yellow stripes (पीली धारियां)": "Yellow Rust: Spray Propiconazole 25% EC.",
        "Brown spots (भूरे धब्बे)": "Leaf Blight: Use Mancozeb 75 WP.",
        "White powder (सफेद पाउडर)": "Powdery Mildew: Use Sulphur 80% WP."
    },
    "Rice (धान)": {
        "Drying tips (पत्तियों का सूखना)": "Bacterial Blight: Apply Streptocycline.",
        "Holes in stems (तने में छेद)": "Stem Borer: Use Carbofuran 3G.",
        "Yellowing plant (पौधा पीला पड़ना)": "Zinc Deficiency: Use Zinc Sulphate."
    }
}

SCHEMES = {
    "Central": [{"Name": "PM-KISAN", "Ben": "₹2,000 (Feb 2026)", "Link": "https://pmkisan.gov.in/"}],
    "State": {
        "Bihar": [{"Name": "Bihar Fasal Sahayata", "Ben": "Crop Insurance", "Link": "https://pacsonline.bih.nic.in/"}],
        "Maharashtra": [{"Name": "Namo Shetkari", "Ben": "₹6,000 Bonus", "Link": "https://nsmny.maharashtra.gov.in/"}],
        "Punjab": [{"Name": "Paani Bachao", "Ben": "Electricity Cashback", "Link": "https://pspcl.in/"}]
    }
}

# --- 3. CORE FUNCTIONS ---
def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    try:
        r = requests.get(url, timeout=5).json()
        return {"temp": r['main']['temp'], "desc": r['weather'][0]['description'], "hum": r['main']['humidity']}
    except: return {"temp": 28, "desc": "clear sky", "hum": 50}

def create_unicode_pdf(farmer, dist, crop, bags):
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    font_path = "gargi.ttf" 
    if os.path.exists(font_path):
        pdf.add_font('HindiFont', '', font_path)
        pdf.set_font('HindiFont', size=14)
    else:
        pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "AGRI-SMART REPORT 2026", ln=1, align='C')
    pdf.cell(0, 10, f"Farmer: {farmer}", ln=1)
    pdf.cell(0, 10, f"District: {dist}", ln=1)
    pdf.cell(0, 10, f"Crop: {crop}", ln=1)
    pdf.cell(0, 10, f"Urea Bags: {bags}", ln=1)
    return pdf.output()

# --- 4. LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title("🚜 A.S.E Login")
    u_name = st.text_input("Type Farmer Name / किसान का नाम लिखें")
    if st.button("Start Dashboard / डैशबोर्ड शुरू करें") and u_name:
        st.session_state.auth, st.session_state.user = True, u_name
        st.rerun()
else:
    lang = st.sidebar.radio("Language / भाषा", ["English", "Hindi"])
    txt = content[lang]
    selected_dist = st.sidebar.selectbox(txt["district_label"], DISTRICTS)
    
    # NEW SYNC BUTTON
    if st.sidebar.button(txt["sync"]):
        st.cache_data.clear()
        st.toast("Weather Updated!")

    w_data = get_weather(selected_dist)

    st.title(txt["title"])
    st.write(f"👋 **{st.session_state.user}** | {datetime.now().strftime('%d %B %Y')}")

    tabs = st.tabs([txt["weather"], txt["soil"], txt["pests"], txt["mandi"], txt["schemes"]])

    with tabs[0]:
        c1, c2 = st.columns(2)
        c1.metric("Temp", f"{w_data['temp']}°C")
        c2.metric("Humidity", f"{w_data['hum']}%")
        if "rain" in w_data['desc'].lower(): 
            st.error("⚠️ RAIN DETECTED: AVOID FERTILIZERS")
        
        st.subheader("📍 Field GPS Map")
        m = folium.Map(location=[25.59, 85.13], zoom_start=12)
        folium.Marker([25.59, 85.13]).add_to(m)
        st_folium(m, height=200, use_container_width=True)

    with tabs[1]:
        st.header(txt["soil"])
        crop_sel = st.selectbox(txt["crop_label"], list(PEST_DB.keys()))
        acres = st.slider("Acres / एकड़", 0.5, 50.0, 1.0)
        urea_bags = round(acres * 1.5, 1)
        st.metric(txt["urea"], urea_bags)
        
        
        if st.download_button(txt["report"], create_unicode_pdf(st.session_state.user, selected_dist, crop_sel, urea_bags), "Report.pdf"):
            st.toast("PDF Saved!")

    with tabs[2]:
        st.header(txt["pests"])
        issues = list(PEST_DB[crop_sel].keys())
        selected_issue = st.selectbox(txt["issue_label"], ["-- Choose --"] + issues)
        if selected_issue != "-- Choose --":
            st.warning(f"**{txt['solution']}:** {PEST_DB[crop_sel][selected_issue]}")
        

    with tabs[3]:
        st.header(txt["mandi"])
        prices = [2100 + random.randint(-40, 60) for _ in range(7)]
        st.plotly_chart(go.Figure(go.Scatter(y=prices, mode='lines+markers', line_color='green')), use_container_width=True)

    with tabs[4]:
        st.header(txt["schemes"])
        state_map = {"Patna": "Bihar", "Gaya": "Bihar", "Pune": "Maharashtra", "Amritsar": "Punjab"}
        curr_state = state_map.get(selected_dist, "Bihar")
        for s in SCHEMES["Central"] + SCHEMES["State"].get(curr_state, []):
            st.markdown(f"✅ **{s['Name']}**: {s['Ben']} | [**{txt['apply']}**]({s['Link']})")

    st.divider()
    st.markdown(f'📞 [Call Tractor Rental](tel:9876543210) | 💬 [SMS Support](sms:9876543210)')
