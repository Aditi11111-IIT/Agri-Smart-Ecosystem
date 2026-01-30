import streamlit as st
import pandas as pd
import requests
import random
from fpdf import FPDF
from datetime import datetime
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go

# --- 1. SETTINGS & BILINGUAL DICTIONARY ---
st.set_page_config(page_title="Agri-Smart Ecosystem 2026", layout="wide", page_icon="🌾")
API_KEY = "44ce6d6e018ff31baf4081ed56eb7fb7" 

content = {
    "English": {
        "title": "🚜 Agri-Smart Ecosystem",
        "weather": "Weather & Alerts",
        "soil": "Soil & Fertilizer",
        "pests": "Pest Diagnosis",
        "mandi": "Mandi Rates",
        "schemes": "Govt Schemes",
        "district": "Enter District",
        "select_crop": "Select Your Crop",
        "select_issue": "What do you see on the plant?",
        "solution": "Recommended Solution",
        "report": "Download Soil Report (PDF)",
        "urea": "Urea Required (50kg Bags)",
        "apply": "Apply Here"
    },
    "Hindi": {
        "title": "🚜 एग्री-स्मार्ट इकोसिस्टम",
        "weather": "मौसम और अलर्ट",
        "soil": "मिट्टी और उर्वरक",
        "pests": "कीट और रोग उपचार",
        "mandi": "मंडी भाव",
        "schemes": "सरकारी योजनाएं",
        "district": "अपना जिला दर्ज करें",
        "select_crop": "अपनी फसल चुनें",
        "select_issue": "पौधे पर आप क्या देख रहे हैं?",
        "solution": "सुझाया गया समाधान",
        "report": "मिट्टी की रिपोर्ट डाउनलोड करें (PDF)",
        "urea": "यूरिया की आवश्यकता (50 किलो बोरी)",
        "apply": "यहाँ आवेदन करें"
    }
}

# --- 2. DATABASES ---
PEST_DATA = {
    "Wheat (गेहूँ)": {
        "Yellow stripes (पीली धारियां)": "Yellow Rust: Spray Propiconazole 25% EC.",
        "Brown spots (भूरे धब्बे)": "Leaf Blight: Use Mancozeb 75 WP."
    },
    "Rice (धान)": {
        "Drying leaf tips (पत्तियों का सूखना)": "Bacterial Blight: Apply Streptocycline.",
        "Holes in stems (तने में छेद)": "Stem Borer: Use Carbofuran 3G."
    }
}

SCHEMES = {
    "Central": [{"Name": "PM-KISAN", "Ben": "₹2,000 (Feb 2026)", "Link": "https://pmkisan.gov.in/"}],
    "State": {
        "Bihar": [{"Name": "Bihar Fasal Sahayata", "Ben": "Crop Insurance", "Link": "https://pacsonline.bih.nic.in/"}],
        "Maharashtra": [{"Name": "Namo Shetkari", "Ben": "₹6,000 Bonus", "Link": "https://nsmny.maharashtra.gov.in/"}]
    }
}

# --- 3. HELPER FUNCTIONS ---
def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    try:
        r = requests.get(url, timeout=5).json()
        return {"temp": r['main']['temp'], "desc": r['weather'][0]['description'], "hum": r['main']['humidity']}
    except: return {"temp": 28, "desc": "clear sky", "hum": 50}

def create_pdf(farmer, dist, crop, bags):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "OFFICIAL AGRI-SMART SOIL REPORT", ln=1, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Farmer Name: {farmer}", ln=1)
    pdf.cell(0, 10, f"District: {dist}", ln=1)
    pdf.cell(0, 10, f"Selected Crop: {crop}", ln=1)
    pdf.cell(0, 10, f"Total Urea Bags Recommended: {bags}", ln=1)
    return pdf.output(dest='S').encode('latin-1')

# --- 4. MAIN APP ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title("🚜 A.S.E Secure Login / लॉगिन")
    u_name = st.text_input("Name / नाम")
    if st.button("Enter / प्रवेश"):
        st.session_state.auth, st.session_state.user = True, u_name
        st.rerun()
else:
    lang = st.sidebar.radio("Language / भाषा", ["English", "Hindi"])
    txt = content[lang]
    dist = st.sidebar.text_input(txt["district"], "Patna")
    w_data = get_weather(dist)

    st.title(txt["title"])
    st.write(f"👋 {st.session_state.user} | {datetime.now().strftime('%d %B %Y')}")

    # WEATHER ALERT BOX
    if "rain" in w_data["desc"].lower():
        st.error(f"⚠️ {w_data['desc'].upper()}! Do NOT apply fertilizer today.")
    else:
        st.success(f"✅ Weather: {w_data['desc'].title()}. Safe for field work.")

    tabs = st.tabs([txt["weather"], txt["soil"], txt["pests"], txt["mandi"], txt["schemes"]])

    with tabs[0]:
        c1, c2 = st.columns(2)
        c1.metric("Temperature", f"{w_data['temp']}°C")
        c2.metric("Humidity", f"{w_data['hum']}%")
        st.subheader("📍 Field Location (GPS Mapping)")
        m = folium.Map(location=[25.59, 85.13], zoom_start=12)
        folium.Marker([25.59, 85.13], popup="Your Farm").add_to(m)
        st_folium(m, height=200, use_container_width=True)

    with tabs[1]:
        st.header(txt["soil"])
        crop_sel = st.selectbox(txt["select_crop"], ["Wheat (गेहूँ)", "Rice (धान)"])
        acres = st.number_input("Acres / एकड़", 0.5, 100.0, 1.0)
        urea_bags = round(acres * 1.5, 1)
        st.metric(txt["urea"], urea_bags)
        
        if st.download_button(txt["report"], create_pdf(st.session_state.user, dist, crop_sel, urea_bags), "Report.pdf"):
            st.toast("PDF Generated!")

    with tabs[2]:
        st.header(txt["pests"])
        issue_list = list(PEST_DATA.get(crop_sel, {}).keys())
        selected_issue = st.selectbox(txt["select_issue"], ["-- Select --"] + issue_list)
        if selected_issue != "-- Select --":
            st.info(f"**{txt['solution']}:** {PEST_DATA[crop_sel][selected_issue]}")
        

    with tabs[3]:
        st.header(txt["mandi"])
        prices = [2100 + random.randint(-50, 50) for _ in range(7)]
        st.plotly_chart(go.Figure(go.Scatter(y=prices, mode='lines+markers')), use_container_width=True)
        st.write(f"Current Market Rate: ₹{prices[-1]}/quintal")

    with tabs[4]:
        st.header(txt["schemes"])
        state_key = "Bihar" if dist in ["Patna", "Gaya"] else "Maharashtra"
        for s in SCHEMES["Central"] + SCHEMES["State"].get(state_key, []):
            st.markdown(f"✅ **{s['Name']}**: {s['Ben']} | [**{txt['apply']}**]({s['Link']})")

    st.divider()
    st.subheader("🚜 Machinery Rental (Instant Call)")
    st.markdown(f'📞 [Call Tractor Owner](tel:9876543210) | 💬 [SMS Support](sms:9876543210)')
